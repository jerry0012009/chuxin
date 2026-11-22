package chuxin;

import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ChuxinApplicationStructureTest {

    @Test
    void springBootApplicationLivesAtProjectRootPackage() throws Exception {
        Class<?> applicationClass = Class.forName("chuxin.ChuxinApplication");

        assertThat(applicationClass.getPackageName()).isEqualTo("chuxin");
        assertThat(applicationClass.getAnnotation(SpringBootApplication.class)).isNotNull();
    }

    @Test
    void authModuleDoesNotOwnTheProjectApplicationEntryPoint() {
        assertThatThrownBy(() -> Class.forName("chuxin.auth.AuthServiceApplication"))
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    void oldComPackageDoesNotOwnTheProjectApplicationEntryPoint() {
        assertThatThrownBy(() -> Class.forName("com.chuxin.ChuxinApplication"))
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    void backendRuntimeUsesXinyuCareAlignedModuleBoundaries() throws Exception {
        assertThat(Class.forName("chuxin.auth.AuthController").getPackageName()).isEqualTo("chuxin.auth");
        assertThat(Class.forName("chuxin.auth.AuthService").getPackageName()).isEqualTo("chuxin.auth");
        assertThat(Class.forName("chuxin.db.DataController").getPackageName()).isEqualTo("chuxin.db");
        assertThat(Class.forName("chuxin.db.GenericDataService").getPackageName()).isEqualTo("chuxin.db");
        assertThat(Class.forName("chuxin.scale.ScaleAssessmentController").getPackageName()).isEqualTo("chuxin.scale");
        assertThat(Class.forName("chuxin.scale.ScaleAssessmentService").getPackageName()).isEqualTo("chuxin.scale");
        assertThat(Class.forName("chuxin.neuropsych.NeuropsychAssessmentController").getPackageName()).isEqualTo("chuxin.neuropsych");
        assertThat(Class.forName("chuxin.neuropsych.NeuropsychAssessmentService").getPackageName()).isEqualTo("chuxin.neuropsych");
        assertThat(Class.forName("chuxin.brainintervention.BrainInterventionReportController").getPackageName()).isEqualTo("chuxin.brainintervention");
        assertThat(Class.forName("chuxin.brainintervention.BrainInterventionReportService").getPackageName()).isEqualTo("chuxin.brainintervention");
        assertThat(Class.forName("chuxin.assessmenttasks.AssessmentPublishTaskController").getPackageName()).isEqualTo("chuxin.assessmenttasks");
        assertThat(Class.forName("chuxin.assessmenttasks.AssessmentPublishTaskService").getPackageName()).isEqualTo("chuxin.assessmenttasks");
        assertThat(Class.forName("chuxin.storage.StorageController").getPackageName()).isEqualTo("chuxin.storage");
        assertThat(Class.forName("chuxin.functions.FunctionController").getPackageName()).isEqualTo("chuxin.functions");
        assertThat(Class.forName("chuxin.common.HealthController").getPackageName()).isEqualTo("chuxin.common");
        assertThatThrownBy(() -> Class.forName("chuxin.profile.Profile"))
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    void speechRecognitionUsesXinyuCareOpenRouterAudioTranscriptionBoundary() throws Exception {
        String source = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/java/chuxin/functions/AiService.java"
        ));

        assertThat(source).contains("https://openrouter.ai/api/v1/audio/transcriptions");
        assertThat(source).contains("\"input_audio\", payload.get(\"input_audio\")");
    }

    @Test
    void legacyChuxinJpaSlicesAreNoLongerTheRuntimeBaseline() {
        assertThatThrownBy(() -> Class.forName("chuxin.auth.api.AccountController"))
                .isInstanceOf(ClassNotFoundException.class);
        assertThatThrownBy(() -> Class.forName("chuxin.auth.model.AuthUser"))
                .isInstanceOf(ClassNotFoundException.class);
        assertThatThrownBy(() -> Class.forName("chuxin.emotion.EmotionRecord"))
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    void scaleAssessmentMigrationDefinesIndependentTablesAndReservedNeuropsychType() throws Exception {
        String migration = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V4__scale_assessment.sql"
        ));

        assertThat(migration).contains("CREATE TABLE IF NOT EXISTS scale_surveys");
        assertThat(migration).contains("CREATE TABLE IF NOT EXISTS scale_distribution_records");
        assertThat(migration).contains("assessment_category ENUM('scale','neuropsych')");
    }

    @Test
    void neuropsychMigrationDefinesTestsRecordsAndAssessmentPublishTasks() throws Exception {
        String migration = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V5__neuropsych_and_task_publishing.sql"
        ));

        assertThat(migration).contains("CREATE TABLE IF NOT EXISTS neuropsych_tests");
        assertThat(migration).contains("CREATE TABLE IF NOT EXISTS neuropsych_records");
        assertThat(migration).contains("CREATE TABLE IF NOT EXISTS assessment_publish_batches");
        assertThat(migration).contains("go-nogo");
        assertThat(migration).contains("columbia-card-task-hot");
        assertThat(migration).contains("discount-titrate");
    }

    @Test
    void neuropsychDemoMigrationDefinesShortExperienceTasks() throws Exception {
        String migration = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V6__neuropsych_demo_tests.sql"
        ));

        assertThat(migration).contains("go-nogo-demo");
        assertThat(migration).contains("columbia-card-task-hot-demo");
        assertThat(migration).contains("discount-titrate-demo");
        assertThat(migration).contains("estimated_minutes");
    }

    @Test
    void neuropsychMobileControlMigrationDefinesTouchControls() throws Exception {
        String v7 = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V7__neuropsych_mobile_controls.sql"
        ));
        String v8 = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V8__neuropsych_mobile_advance_controls.sql"
        ));
        String v9 = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V9__neuropsych_cct_compact_mobile_controls.sql"
        ));
        String migration = v7 + "\n" + v8 + "\n" + v9;

        assertThat(migration).contains("mobileControls");
        assertThat(migration).contains("\"command\": \"advance\"");
        assertThat(migration).contains("clickFirstAvailableCard");
        assertThat(migration).contains("KeyQ");
        assertThat(migration).contains("Space");
        assertThat(v9).contains("columbia-card-task-hot-demo");
        assertThat(v9).contains("回车/继续");
    }

    @Test
    void brainInterventionReportMigrationDefinesFlexibleReportTable() throws Exception {
        String migration = java.nio.file.Files.readString(java.nio.file.Path.of(
                "src/main/resources/db/migration/V22__brain_intervention_reports.sql"
        ));

        assertThat(migration).contains("CREATE TABLE IF NOT EXISTS brain_intervention_reports");
        assertThat(migration).contains("report_type VARCHAR(64)");
        assertThat(migration).contains("task_type VARCHAR(64)");
        assertThat(migration).contains("metrics_json JSON NULL");
        assertThat(migration).contains("curve_json JSON NULL");
        assertThat(migration).contains("config_json JSON NULL");
    }
}
