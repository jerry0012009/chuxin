package chuxin.db;

public record FilterCondition(
    String op,
    String field,
    Object value
) {
}
