// Runs every [Fact] and [Theory] in this assembly the way xUnit does: a new instance of the class per test.
using System.Reflection;
using Xunit;

var only = args.Length > 0 ? args[0] : null;
int passed = 0, failed = 0;
foreach (var type in Assembly.GetExecutingAssembly().GetTypes().OrderBy(t => t.FullName, StringComparer.Ordinal))
{
    foreach (var method in type.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly).OrderBy(m => m.Name, StringComparer.Ordinal))
    {
        var isFact = method.GetCustomAttribute<FactAttribute>() is not null;
        var isTheory = method.GetCustomAttribute<TheoryAttribute>() is not null;
        if (!isFact && !isTheory)
            continue;
        if (only is not null && !type.Name.Contains(only, StringComparison.Ordinal))
            continue;
        List<object?[]> rows = [[]];
        if (isTheory)
        {
            rows = method.GetCustomAttributes<InlineDataAttribute>().Select(a => a.Data).ToList();
            foreach (var member in method.GetCustomAttributes<MemberDataAttribute>())
            {
                var property = type.GetProperty(member.MemberName, BindingFlags.Public | BindingFlags.Static)
                    ?? throw new InvalidOperationException($"{type.Name}.{member.MemberName} is not a public static property");
                rows.AddRange(((IEnumerable<object[]>)property.GetValue(null)!).Select(row => (object?[])row));
            }
            if (rows.Count == 0)
                throw new InvalidOperationException($"{type.Name}.{method.Name} is a theory with no rows");
        }
        foreach (var row in rows)
        {
            var name = $"{type.Name}.{method.Name}" + (isTheory ? $"({string.Join(", ", row.Select(v => v is string s ? $"\"{s}\"" : v))})" : "");
            try
            {
                var instance = Activator.CreateInstance(type);
                if (method.Invoke(instance, row) is Task task)
                    await task;
                passed++;
                Console.WriteLine($"PASS  {name}");
            }
            catch (Exception ex)
            {
                failed++;
                var cause = ex is TargetInvocationException { InnerException: { } inner } ? inner : ex;
                Console.WriteLine($"FAIL  {name}\n      {cause.GetType().Name}: {cause.Message}");
            }
        }
    }
}

Console.WriteLine($"\n{passed} passed, {failed} failed");
return failed == 0 ? 0 : 1;
