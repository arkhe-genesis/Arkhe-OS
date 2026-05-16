package test.platform;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.lang.ArchRule;
import org.junit.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;

public class ArkheOSArchitectureTest {
    @Test
    public void some_architecture_rule() {
        JavaClasses importedClasses = new ClassFileImporter().importPackages("com.arkhe.os");

        ArchRule rule = classes()
            .that().resideInAPackage("..adapters..")
            .should().haveSimpleNameEndingWith("Adapter");

        rule.check(importedClasses);
    }
}
