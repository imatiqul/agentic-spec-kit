// Stand-in for src/HealthQCopilot.Infrastructure/Persistence/AuditDbContext.cs. The real one maps the table
// with EF Core's model builder, which needs the EF Core packages. The record's shape is copied from it.
using Microsoft.EntityFrameworkCore;

namespace HealthQCopilot.Infrastructure.Persistence;

public class AuditDbContext(DbContextOptions<AuditDbContext> options) : DbContext(options)
{
    public DbSet<PhiAuditLog> PhiAuditLogs => Set<PhiAuditLog>();
}

public sealed class PhiAuditLog
{
    public Guid Id { get; set; }
    public string UserId { get; set; } = string.Empty;
    public string HttpMethod { get; set; } = string.Empty;
    public string ResourcePath { get; set; } = string.Empty;
    public int StatusCode { get; set; }
    public string? CorrelationId { get; set; }
    public DateTime AccessedAt { get; set; }
}
