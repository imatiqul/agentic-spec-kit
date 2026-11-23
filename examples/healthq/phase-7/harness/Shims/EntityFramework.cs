// Stand-in for EF Core's in-memory provider, as far as the tests use it: rows are kept per database name,
// an added row is visible only after SaveChangesAsync, and each context reads what was saved.
using System.Collections;
using System.Collections.Concurrent;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.EntityFrameworkCore
{
    public class DbContextOptions
    {
        public string DatabaseName { get; set; } = "";
    }

    public class DbContextOptions<TContext> : DbContextOptions where TContext : DbContext;

    public class DbContextOptionsBuilder
    {
        protected DbContextOptions Current { get; init; } = new();
        public virtual DbContextOptions Options => Current;
        internal void Name(string name) => Current.DatabaseName = name;
    }

    public class DbContextOptionsBuilder<TContext> : DbContextOptionsBuilder where TContext : DbContext
    {
        public DbContextOptionsBuilder() => Current = new DbContextOptions<TContext>();
        public new DbContextOptions<TContext> Options => (DbContextOptions<TContext>)Current;
    }

    public static class InMemoryDbContextOptionsExtensions
    {
        public static DbContextOptionsBuilder UseInMemoryDatabase(this DbContextOptionsBuilder builder, string databaseName)
        {
            builder.Name(databaseName);
            return builder;
        }

        public static DbContextOptionsBuilder<TContext> UseInMemoryDatabase<TContext>(this DbContextOptionsBuilder<TContext> builder, string databaseName)
            where TContext : DbContext
        {
            builder.Name(databaseName);
            return builder;
        }
    }

    public abstract class DbContext(DbContextOptions options) : IDisposable, IAsyncDisposable
    {
        private static readonly ConcurrentDictionary<(string Database, Type Entity), IList> Saved = new();
        private readonly List<(Type Entity, object Row)> _pending = [];

        internal IList Rows(Type entity) => Saved.GetOrAdd((options.DatabaseName, entity), _ => ArrayList.Synchronized(new ArrayList()));
        internal void Track(Type entity, object row) => _pending.Add((entity, row));

        public DbSet<TEntity> Set<TEntity>() where TEntity : class => new(this);

        public Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
        {
            foreach (var (entity, row) in _pending)
                Rows(entity).Add(row);
            var count = _pending.Count;
            _pending.Clear();
            return Task.FromResult(count);
        }

        public void Dispose() => GC.SuppressFinalize(this);

        public ValueTask DisposeAsync()
        {
            GC.SuppressFinalize(this);
            return ValueTask.CompletedTask;
        }
    }

    public sealed class DbSet<TEntity>(DbContext context) : IEnumerable<TEntity> where TEntity : class
    {
        public void Add(TEntity entity) => context.Track(typeof(TEntity), entity);

        public IEnumerator<TEntity> GetEnumerator()
        {
            var rows = context.Rows(typeof(TEntity));
            lock (rows.SyncRoot)
                return rows.Cast<TEntity>().ToList().GetEnumerator();
        }

        IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    }

    public static class EntityFrameworkQueryableExtensions
    {
        public static Task<int> CountAsync<T>(this IEnumerable<T> source, CancellationToken cancellationToken = default) => Task.FromResult(source.Count());
        public static Task<List<T>> ToListAsync<T>(this IEnumerable<T> source, CancellationToken cancellationToken = default) => Task.FromResult(source.ToList());
        public static Task<T?> SingleOrDefaultAsync<T>(this IEnumerable<T> source, CancellationToken cancellationToken = default) => Task.FromResult(source.SingleOrDefault());
    }
}

namespace Microsoft.Extensions.DependencyInjection
{
    using Microsoft.EntityFrameworkCore;

    public static class EntityFrameworkServiceCollectionExtensions
    {
        public static IServiceCollection AddDbContext<TContext>(this IServiceCollection services, Action<DbContextOptionsBuilder> optionsAction)
            where TContext : DbContext
        {
            var builder = new DbContextOptionsBuilder<TContext>();
            optionsAction(builder);
            return services.AddScoped(_ => (TContext)Activator.CreateInstance(typeof(TContext), builder.Options)!);
        }
    }
}
