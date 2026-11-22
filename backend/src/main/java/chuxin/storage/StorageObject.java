package chuxin.storage;

public record StorageObject(
    String bucket,
    String path,
    String publicUrl
) {
}
