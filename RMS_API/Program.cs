using Asp.Versioning;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using RMS_API.CustomClass;
using RMS_API.Data;
using RMS_API.Models;
using RMS_API.Services;
using System.Collections.Concurrent;
using System.Security.Claims;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Configure API versioning  more info https://dev.to/azzdcl/aspnet-core-web-api-with-swagger-api-versioning-for-dotnet-8-3c9j
builder.Services.AddApiVersioning(options =>
    {
        options.AssumeDefaultVersionWhenUnspecified = true; // Assumes the default version if none is specified
        options.DefaultApiVersion = new ApiVersion(1, 0);   // Set the default API version to 1.0
        options.ReportApiVersions = true;                   // Report the API versions supported by the application
    })
    .AddApiExplorer(
    options =>
    {
        options.GroupNameFormat = "'v'VVV";
        options.SubstituteApiVersionInUrl = true;
    });

// Configure Entity Framework Core with SQL Server more info https://learn.microsoft.com/en-us/aspnet/core/data/ef-rp/intro?view=aspnetcore-8.0
builder.Services.AddDbContext<ApplicationDbContext>(options =>
	options.UseSqlServer(builder.Configuration.GetConnectionString("BaseAddress")));


// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

//Add SignalR services more info https://learn.microsoft.com/en-us/aspnet/core/signalr/introduction?view=aspnetcore-8.0
builder.Services.AddSignalR();

//To Add Cors policy
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(
        builder =>
        {
            builder
                    .WithOrigins("http://127.0.0.1:5500")
                   .AllowAnyHeader()
                   .AllowAnyMethod()
                   .AllowCredentials();
        });
});

//Add a dictionary as a singleton to map the connection id with the token
builder.Services.AddSingleton(new ConcurrentDictionary<string, string>());


// Read the connection string
var BaseAddress = builder.Configuration.GetConnectionString("BaseAddress");

//Add imemoryCache along with memory cache
builder.Services.AddMemoryCache();
builder.Services.AddScoped<ICustomMemoryCache, CustomMemoryCache>();

//Add datahandler as transient
builder.Services.AddTransient<IDataHandler>(ServiceProvider =>
{
    // Read the connection string
    var connectionString = builder.Configuration.GetConnectionString("BaseAddress");
    return new DatabaseHelper(connectionString);
});

// Configure JWT settings
builder.Services.Configure<JwtSettings>(builder.Configuration.GetSection("JwtSettings"));

// Inject JwtSettings using IOptions
builder.Services.AddSingleton<IJwtAuth>(serviceProvider =>
{
    var jwtSettings = serviceProvider.GetRequiredService<IOptions<JwtSettings>>();
    return new JwtAuth(jwtSettings);
});

// Configure JWT authentication
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        var serviceProvider = builder.Services.BuildServiceProvider();
        var jwtSettings = serviceProvider.GetRequiredService<IOptions<JwtSettings>>().Value;
        var key = Encoding.ASCII.GetBytes(jwtSettings.SecretKey);

        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true, // Validates token expiry
            ValidateIssuerSigningKey = true,
            ValidIssuer = jwtSettings.Issuer,
            ValidAudience = jwtSettings.Audience,
            IssuerSigningKey = new SymmetricSecurityKey(key)
        };

        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = context =>
            {
                var claimsIdentity = context.Principal.Identity as ClaimsIdentity;
                var userIdClaim = claimsIdentity?.FindFirst(ClaimTypes.NameIdentifier);
                var usernameClaim = claimsIdentity?.FindFirst(ClaimTypes.Name);

                if (userIdClaim != null && usernameClaim != null)
                {
                    var user = new AuthenticatedUser
                    {
                        UserId = userIdClaim.Value,
                        Username = usernameClaim.Value
                    };

                    // Add the user object to the HttpContext items
                    context.HttpContext.Items["User"] = user;
                }

                return Task.CompletedTask;
            },
            OnAuthenticationFailed = context =>
            {
                // Log the exception
                context.NoResult();
                context.Response.StatusCode = 500;
                context.Response.ContentType = "text/plain";
                return context.Response.WriteAsync(context.Exception.ToString());
            }
        };
    });



var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

//To use authentication
app.UseAuthentication();

app.UseAuthorization();

app.UseCors();

app.MapControllers();

app.MapHub<MessageHub>("/messagehub");

app.Run();
