package com.arkhe.os.sophon.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "braid_circuits")
@Getter
@Setter
public class BraidCircuit {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 1024)
    private String braidWord;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String jonesMatrixJson;

    @Column(nullable = false)
    private Double jonesReal;

    @Column(nullable = false)
    private Double jonesImag;

    @Column(nullable = false, length = 64)
    private String integrityHash;

    @Column(nullable = false)
    private Integer gateCount;

    @Column
    private String circuitType;

    @Column(nullable = false)
    private Instant compiledAt;
}
