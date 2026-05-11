package test.platform;

import com.arkhe.os.platform.PlatformAbstractionLayer;
import com.arkhe.os.platform.PlatformType;

public abstract class PlatformTestFramework {

    protected PlatformAbstractionLayer platform;
    protected PlatformType platformType;
    protected Object config;

    void setUp() {
        // setup
    }

    protected void assertPlatformOperation(String description, Runnable operation) {
        operation.run();
    }
}
