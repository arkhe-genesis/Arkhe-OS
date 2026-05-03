package com.arkhe.os.sophon;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.kafka.core.KafkaTemplate;
import com.arkhe.os.sophon.repository.SophonPacketRepository;
import com.arkhe.os.sophon.repository.CoherenceMetricRepository;
import com.arkhe.os.sophon.repository.BraidCircuitRepository;
import javax.sql.DataSource;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "spring.kafka.bootstrap-servers=localhost:9092"
})
@ActiveProfiles("test")
public class IntegrationTest {

    @MockBean
    private KafkaTemplate kafkaTemplate;

    @Test
    void contextLoads() {
    }
}
