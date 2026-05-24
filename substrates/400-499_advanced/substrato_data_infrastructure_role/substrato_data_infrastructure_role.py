import json
import tempfile
import os

class SubstratoDataInfrastructureRole:
    def canonize(self):
        report = {
            "Overview": "You'll build the data infrastructure that turns raw signals into the training data Arkhe's models learn from, and the pipelines that keep it flowing at scale. That means owning the full data engineering stack: ingestion, transformation, quality filtering, and delivery to training and evaluation systems. The models we ship are only as good as the data behind them, and this role owns that foundation. This is a high-ownership role on a small team. You'll work directly with model researchers, data collection leads, and infrastructure engineers, and the systems you build will directly shape the quality and pace of model development.",
            "Responsibilities": [
                "Design and build scalable data pipelines that ingest, process, and deliver training data across multiple modalities: text, audio, vision, and structured feedback signals.",
                "Own the data infrastructure stack end-to-end: ingestion, transformation, deduplication, quality filtering, versioning, and delivery to model training and evaluation systems.",
                "Collaborate closely with model researchers and data collection leads to understand data requirements and translate them into reliable, auditable pipelines.",
                "Build tooling and frameworks that make it easy for the team to inspect, evaluate, and iterate on data quality. The insights surfaced should feed back into collection and curation decisions.",
                "Define and enforce data quality standards. Instrument pipelines for correctness, freshness, and coverage. Catch regressions before they reach training.",
                "Design data systems for reproducibility and scale. The pipelines you build need to handle growing volumes across modalities without becoming a bottleneck.",
                "Identify gaps in the current stack and drive concrete improvements to throughput, quality, and reliability."
            ],
            "Requirements": [
                "Strong data engineering fundamentals. You are comfortable designing and operating large-scale batch and streaming pipelines, and you care about correctness and reliability.",
                "Experience building data systems for machine learning. You understand the difference between a data pipeline for analytics and one that feeds model training, and you know what it takes to get the latter right.",
                "Fluency with the modern data stack. You've worked with tools like Spark, Beam, or Flink, and you know how to make tradeoffs between them. Experience with data versioning systems (e.g., DVC, Delta Lake, Iceberg) is a strong plus.",
                "Systems thinking. You reason about schema evolution, backfills, and failure modes before they become production incidents. You build for the day-2 case, not just the demo.",
                "A quality instinct. You don't just move data. You understand what's in it, catch problems early, and close the feedback loop with the people who need clean data.",
                "Strong communication. You can work closely with model researchers and engineers, explain data tradeoffs clearly, and make good decisions across team boundaries.",
                "5+ years of relevant data engineering experience. Experience at a fast-growing AI or research-driven company is a strong plus."
            ],
            "Bonus_Qualifications": [
                "Experience building data infrastructure for large language model or multimodal model training.",
                "Familiarity with multimodal data formats and processing pipelines (audio, video, image).",
                "Experience with human feedback or preference data pipelines (RLHF, DPO, or similar).",
                "Hands-on experience with data quality evaluation frameworks or annotation tooling.",
                "Background in distributed systems, stream processing, or large-scale ETL.",
                "Experience at a fast-moving AI lab or research-driven company."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_data_infrastructure_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Data Infrastructure Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoDataInfrastructureRole()
    substrate.canonize()
