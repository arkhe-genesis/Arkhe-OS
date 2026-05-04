package com.arkhe.os.sophon.repository;

import com.arkhe.os.sophon.model.BraidCircuit;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface BraidCircuitRepository extends CrudRepository<BraidCircuit, UUID> {
    Optional<BraidCircuit> findByBraidWord(String braidWord);
}
