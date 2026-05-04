package com.arkhe.os.sophon.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "sophon_packets", indexes = {
    @Index(name = "idx_dest_hash", columnList = "destinationHash"),
    @Index(name = "idx_session_id", columnList = "sessionId"),
    @Index(name = "idx_timestamp", columnList = "timestamp")
})
@Getter
@Setter
public class SophonPacket {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private Double chronometricPreamble;

    @Column(nullable = false, length = 64)
    private String destinationHash;

    @Column(nullable = false, length = 64)
    private String sourceHash;

    @Column(columnDefinition = "TEXT")
    private String gluingVector;

    @Column(length = 64)
    private String sessionId;

    @Lob
    @Column(nullable = false)
    private byte[] payload;

    @Column(nullable = false, length = 64)
    private String payloadIntegrityHash;

    @Column(nullable = false)
    private Double phiManifestation;

    @Column(length = 32)
    private String proofType;

    @Column(nullable = false)
    private Instant timestamp;
}
