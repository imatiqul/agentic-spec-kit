// Stand-in for the four xUnit attributes the tests use.
namespace Xunit;

[AttributeUsage(AttributeTargets.Method)]
public sealed class FactAttribute : Attribute;

[AttributeUsage(AttributeTargets.Method)]
public sealed class TheoryAttribute : Attribute;

[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
public sealed class InlineDataAttribute(params object?[] data) : Attribute
{
    public object?[] Data { get; } = data;
}

/// <summary>Rows from a public static property of the test class that returns <c>IEnumerable&lt;object[]&gt;</c>.</summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
public sealed class MemberDataAttribute(string memberName) : Attribute
{
    public string MemberName { get; } = memberName;
}
