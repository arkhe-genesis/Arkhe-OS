package com.arkhe.os.sophon;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
public class SophonNetworkApplication {
    public static void main(String[] args) {
        SpringApplication.run(SophonNetworkApplication.class, args);
    }
}
