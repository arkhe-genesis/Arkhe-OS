package com.arkhe.os.sophon.repository;

import com.arkhe.os.sophon.model.SophonPacket;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface SophonPacketRepository extends CrudRepository<SophonPacket, UUID> {
}
