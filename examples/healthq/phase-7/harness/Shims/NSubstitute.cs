// Stand-in for the NSubstitute calls the tests use: a recording proxy for an interface, a count of the
// calls it received, and a way to make one member throw or return a value.
using System.Reflection;

namespace NSubstitute;

public interface ICall
{
    MethodInfo GetMethodInfo();
    object?[] GetArguments();
}

public sealed class CallInfo(object?[] arguments)
{
    public object?[] Args() => arguments;
}

public sealed class ConfiguredCall;

internal sealed record RecordedCall(MethodInfo Method, object?[] Arguments) : ICall
{
    public MethodInfo GetMethodInfo() => Method;
    public object?[] GetArguments() => Arguments;
}

public class SubstituteProxy : DispatchProxy
{
    [ThreadStatic] internal static SubstituteProxy? LastTarget;
    [ThreadStatic] internal static RecordedCall? LastCall;

    internal readonly List<RecordedCall> Calls = [];
    internal readonly Dictionary<string, Func<CallInfo, object?>> Configured = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)
    {
        var call = new RecordedCall(targetMethod!, args ?? []);
        lock (Calls)
            Calls.Add(call);
        LastTarget = this;
        LastCall = call;
        if (Configured.TryGetValue(targetMethod!.Name, out var configured))
            return configured(new CallInfo(call.Arguments));
        return DefaultFor(targetMethod.ReturnType);
    }

    internal static object? DefaultFor(Type type)
    {
        if (type == typeof(void)) return null;
        if (type == typeof(Task)) return Task.CompletedTask;
        if (type == typeof(ValueTask)) return default(ValueTask);
        return type.IsValueType ? Activator.CreateInstance(type) : null;
    }

    internal List<RecordedCall> Snapshot()
    {
        lock (Calls)
            return [.. Calls];
    }
}

/// <summary>What <c>Received(n)</c> returns: calling a member on it checks how often the substitute received that member.</summary>
public class ReceivedProxy : DispatchProxy
{
    internal SubstituteProxy Target = null!;
    internal int Expected;

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)
    {
        var count = Target.Snapshot().Count(c => c.Method.Name == targetMethod!.Name);
        if (count != Expected)
            throw new InvalidOperationException($"expected {Expected} call(s) to {targetMethod!.Name}, received {count}");
        return SubstituteProxy.DefaultFor(targetMethod!.ReturnType);
    }
}

public static class Substitute
{
    public static T For<T>() where T : class => DispatchProxy.Create<T, SubstituteProxy>();
}

public static class Arg
{
    public static T Any<T>() => default!;
}

public static class SubstituteExtensions
{
    private static SubstituteProxy Proxy(object substitute) =>
        substitute as SubstituteProxy ?? throw new InvalidOperationException("not a substitute");

    public static IEnumerable<ICall> ReceivedCalls<T>(this T substitute) where T : class => Proxy(substitute).Snapshot();

    public static T Received<T>(this T substitute, int count) where T : class => Expecting(substitute, count);
    public static T ReceivedWithAnyArgs<T>(this T substitute, int count) where T : class => Expecting(substitute, count);
    public static T DidNotReceiveWithAnyArgs<T>(this T substitute) where T : class => Expecting(substitute, 0);

    private static T Expecting<T>(T substitute, int count) where T : class
    {
        var checker = DispatchProxy.Create<T, ReceivedProxy>();
        var proxy = (ReceivedProxy)(object)checker;
        proxy.Target = Proxy(substitute);
        proxy.Expected = count;
        return checker;
    }

    /// <summary>Makes the member that was just called return this value, and forgets that set-up call.</summary>
    public static ConfiguredCall Returns<T>(this T value, T returnThis) => Configure(_ => returnThis);

    /// <summary>Makes the member that was just called run this function, and forgets that set-up call.</summary>
    public static ConfiguredCall Returns<T>(this object? value, Func<CallInfo, T> returnThis) => Configure(info => returnThis(info));

    private static ConfiguredCall Configure(Func<CallInfo, object?> behaviour)
    {
        var target = SubstituteProxy.LastTarget ?? throw new InvalidOperationException("Returns() must follow a call on a substitute");
        var call = SubstituteProxy.LastCall!;
        lock (target.Calls)
            target.Calls.Remove(call);
        target.Configured[call.Method.Name] = behaviour;
        return new ConfiguredCall();
    }
}
