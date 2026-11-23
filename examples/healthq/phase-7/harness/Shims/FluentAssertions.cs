// Stand-in for the FluentAssertions calls the tests use. Same names and shapes; a failed assertion throws.
namespace FluentAssertions;

public sealed class AssertionFailed(string message) : Exception(message);

public static class AssertionExtensions
{
    public static ObjectAssertions Should(this object? actual) => new(actual);
    public static StringAssertions Should(this string? actual) => new(actual);
    public static BooleanAssertions Should(this bool actual) => new(actual);
    public static CollectionAssertions<T> Should<T>(this IEnumerable<T> actual) => new(actual);
    public static AsyncFunctionAssertions Should(this Func<Task> action) => new(action);
}

internal static class Fail
{
    public static void Unless(bool ok, string what, string because, object[] args)
    {
        if (!ok)
            throw new AssertionFailed(what + (because.Length > 0 ? " because " + string.Format(because, args) : ""));
    }
}

public sealed class ObjectAssertions(object? actual)
{
    public void Be(object? expected, string because = "", params object[] args) =>
        Fail.Unless(Equals(actual, expected), $"expected {expected ?? "null"}, found {actual ?? "null"}", because, args);
    public void NotBe(object? unexpected, string because = "", params object[] args) =>
        Fail.Unless(!Equals(actual, unexpected), $"did not expect {unexpected ?? "null"}", because, args);
    public void BeNull(string because = "", params object[] args) =>
        Fail.Unless(actual is null, $"expected null, found {actual}", because, args);
    public void NotBeNull(string because = "", params object[] args) =>
        Fail.Unless(actual is not null, "expected a value, found null", because, args);
}

public sealed class StringAssertions(string? actual)
{
    public void Be(string? expected, string because = "", params object[] args) =>
        Fail.Unless(actual == expected, $"expected \"{expected}\", found \"{actual}\"", because, args);
    public void NotBe(string? unexpected, string because = "", params object[] args) =>
        Fail.Unless(actual != unexpected, $"did not expect \"{unexpected}\"", because, args);
    public void BeNull(string because = "", params object[] args) =>
        Fail.Unless(actual is null, $"expected null, found \"{actual}\"", because, args);
    public void NotBeNull(string because = "", params object[] args) =>
        Fail.Unless(actual is not null, "expected a string, found null", because, args);
    public void StartWith(string expected, string because = "", params object[] args) =>
        Fail.Unless(actual is not null && actual.StartsWith(expected, StringComparison.Ordinal), $"expected \"{actual}\" to start with \"{expected}\"", because, args);
    public void Contain(string expected, string because = "", params object[] args) =>
        Fail.Unless(actual is not null && actual.Contains(expected, StringComparison.Ordinal), $"expected \"{actual}\" to contain \"{expected}\"", because, args);
}

public sealed class BooleanAssertions(bool actual)
{
    public void BeTrue(string because = "", params object[] args) => Fail.Unless(actual, "expected true", because, args);
    public void BeFalse(string because = "", params object[] args) => Fail.Unless(!actual, "expected false", because, args);
}

public sealed class CollectionAssertions<T>(IEnumerable<T> actual)
{
    private readonly List<T> _items = actual.ToList();

    public void BeEmpty(string because = "", params object[] args) =>
        Fail.Unless(_items.Count == 0, $"expected no items, found {_items.Count}", because, args);
    public void NotBeEmpty(string because = "", params object[] args) =>
        Fail.Unless(_items.Count > 0, "expected at least one item", because, args);
    public void HaveCount(int expected, string because = "", params object[] args) =>
        Fail.Unless(_items.Count == expected, $"expected {expected} item(s), found {_items.Count}", because, args);
    public void ContainSingle(string because = "", params object[] args) =>
        Fail.Unless(_items.Count == 1, $"expected exactly one item, found {_items.Count}", because, args);
    public void Equal(params T[] expected) => Equal((IEnumerable<T>)expected);
    public void Equal(IEnumerable<T> expected) =>
        Fail.Unless(_items.SequenceEqual(expected), $"expected [{string.Join(", ", expected)}], found [{string.Join(", ", _items)}]", "", []);
    public void BeEquivalentTo(params T[] expected) =>
        Fail.Unless(_items.Count == expected.Length && !_items.Except(expected).Any() && !expected.Except(_items).Any(),
            $"expected the items [{string.Join(", ", expected)}] in any order, found [{string.Join(", ", _items)}]", "", []);
}

public sealed class AsyncFunctionAssertions(Func<Task> action)
{
    public async Task NotThrowAsync(string because = "", params object[] args)
    {
        try
        {
            await action();
        }
        catch (Exception ex)
        {
            Fail.Unless(false, $"expected no exception, found {ex.GetType().Name}: {ex.Message}", because, args);
        }
    }
}
