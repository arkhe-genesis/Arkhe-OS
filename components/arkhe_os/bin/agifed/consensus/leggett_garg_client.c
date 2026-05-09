/* bin/agifed/consensus/leggett_garg_client.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <linux/agi.h>
#include "../../network/rcp_client.h"
#include "../../network/qkd_client.h"
#include "../../identity/federated_identity.h"

struct lg_consensus_client {
    char *network_id;
    char *node_id;
    struct rcp_client *rcp;
    struct qkd_client *qkd;
    struct federated_identity *identity;
    int min_participants;
    double significance_threshold;
};

struct lg_consensus_client *lg_client_init(const char *network_id, const char *node_id)
{
    struct lg_consensus_client *client = calloc(1, sizeof(*client));
    if (!client) return NULL;

    client->network_id = strdup(network_id);
    client->node_id = strdup(node_id);
    client->min_participants = 3;
    client->significance_threshold = 3.0;  /* 3σ */

    /* Initialize RCP client for retrocausal communication */
    client->rcp = rcp_client_init(node_id);
    if (!client->rcp) goto err;

    /* Initialize QKD client for quantum key distribution */
    client->qkd = qkd_client_init(node_id);
    if (!client->qkd) goto err_rcp;

    /* Initialize federated identity */
    client->identity = federated_identity_init(node_id, client->qkd);
    if (!client->identity) goto err_qkd;

    return client;

err_qkd:
    qkd_client_destroy(client->qkd);
err_rcp:
    rcp_client_destroy(client->rcp);
err:
    free(client->node_id);
    free(client->network_id);
    free(client);
    return NULL;
}

int lg_client_propose_test(struct lg_consensus_client *client,
                          const char *observable,
                          double *time_points,
                          int num_time_points,
                          double target_K,
                          char **proposal_id_out)
{
    if (!client || !observable || !time_points || num_time_points < 3) {
        return -EINVAL;
    }

    /* Generate unique proposal ID */
    char proposal_id[64];
    snprintf(proposal_id, sizeof(proposal_id), "lg_%s_%ld",
             client->node_id, time(NULL));

    /* Build proposal message */
    struct lg_proposal_msg msg = {
        .proposal_id = proposal_id,
        .proposer_node = client->node_id,
        .observable = observable,
        .time_points = time_points,
        .num_time_points = num_time_points,
        .target_K = target_K,
        .confidence_threshold = client->significance_threshold,
        .expiration = time(NULL) + 300,  /* 5 minutes */
    };

    /* Sign proposal with federated identity */
    unsigned char signature[64];
    size_t sig_len = sizeof(signature);
    int ret = federated_identity_sign(client->identity, &msg, sizeof(msg), signature, &sig_len);
    if (ret < 0) {
        fprintf(stderr, "Failed to sign proposal\n");
        return ret;
    }
    msg.signature = signature;
    msg.signature_len = sig_len;

    /* Broadcast proposal via RCP network */
    ret = rcp_client_broadcast(client->rcp, RCP_MSG_LG_PROPOSAL, &msg, sizeof(msg));
    if (ret < 0) {
        fprintf(stderr, "Failed to broadcast proposal\n");
        return ret;
    }

    if (proposal_id_out) {
        *proposal_id_out = strdup(proposal_id);
    }

    printf("Proposed Leggett-Garg test: %s\n", proposal_id);
    return 0;
}

int lg_client_submit_measurement(struct lg_consensus_client *client,
                                const char *proposal_id,
                                double timestamp,
                                const char *observable,
                                double value,
                                double uncertainty)
{
    if (!client || !proposal_id || !observable) {
        return -EINVAL;
    }

    /* Build measurement message */
    struct lg_measurement_msg msg = {
        .proposal_id = proposal_id,
        .node_id = client->node_id,
        .timestamp = timestamp,
        .observable = observable,
        .value = value,
        .uncertainty = uncertainty,
    };

    /* Sign measurement with federated identity */
    unsigned char signature[64];
    size_t sig_len = sizeof(signature);
    int ret = federated_identity_sign(client->identity, &msg, sizeof(msg), signature, &sig_len);
    if (ret < 0) {
        fprintf(stderr, "Failed to sign measurement\n");
        return ret;
    }
    msg.signature = signature;
    msg.signature_len = sig_len;

    /* Submit measurement via RCP */
    ret = rcp_client_send(client->rcp, RCP_MSG_LG_MEASUREMENT, &msg, sizeof(msg), "all_participants");
    if (ret < 0) {
        fprintf(stderr, "Failed to submit measurement\n");
        return ret;
    }

    if (verbose) {
        printf("Submitted measurement for %s: value=%.3f ± %.3f\n",
               observable, value, uncertainty);
    }

    return 0;
}

int lg_client_evaluate_consensus(struct lg_consensus_client *client,
                                const char *proposal_id,
                                struct lg_consensus_result *result)
{
    if (!client || !proposal_id || !result) {
        return -EINVAL;
    }

    /* Request evaluation from network */
    struct lg_evaluate_msg eval_msg = {
        .proposal_id = proposal_id,
        .requester_node = client->node_id,
    };

    /* Sign request */
    unsigned char signature[64];
    size_t sig_len = sizeof(signature);
    int ret = federated_identity_sign(client->identity, &eval_msg, sizeof(eval_msg), signature, &sig_len);
    if (ret < 0) {
        return ret;
    }
    eval_msg.signature = signature;
    eval_msg.signature_len = sig_len;

    /* Send evaluation request */
    ret = rcp_client_send(client->rcp, RCP_MSG_LG_EVALUATE, &eval_msg, sizeof(eval_msg), "consensus_orchestrator");
    if (ret < 0) {
        return ret;
    }

    /* Wait for response (with timeout) */
    struct lg_evaluation_response response;
    ret = rcp_client_receive_with_timeout(client->rcp, RCP_MSG_LG_EVALUATION_RESPONSE,
                                         &response, sizeof(response), 30000);
    if (ret < 0) {
        fprintf(stderr, "Failed to receive evaluation response\n");
        return ret;
    }

    /* Verify response signature */
    ret = federated_identity_verify(client->identity, &response, sizeof(response),
                                  response.signature, response.signature_len);
    if (ret < 0) {
        fprintf(stderr, "Failed to verify response signature\n");
        return -EACCES;
    }

    /* Populate result */
    result->K_global = response.K_global;
    result->sigma_global = response.sigma_global;
    result->threshold = response.threshold;
    result->violation = response.violation;
    result->significance = response.significance;
    result->participating_nodes = response.participating_nodes;
    result->node_count = response.node_count;

    if (verbose) {
        printf("Consensus evaluation for %s: K=%.3f ± %.3f, violation=%s\n",
               proposal_id, result->K_global, result->sigma_global,
               result->violation ? "YES" : "NO");
    }

    return 0;
}

void lg_client_destroy(struct lg_consensus_client *client)
{
    if (!client) return;

    if (client->identity) federated_identity_destroy(client->identity);
    if (client->qkd) qkd_client_destroy(client->qkd);
    if (client->rcp) rcp_client_destroy(client->rcp);
    free(client->node_id);
    free(client->network_id);
    free(client);
}
