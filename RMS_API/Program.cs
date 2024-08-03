using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using RMS_API.CustomClass;
using RMS_API.Models;
using ServiceApp_backend.Classes;
using System.Security.Claims;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Read the connection string
var BaseAddress = builder.Configuration.GetConnectionString("BaseAddress");

//Add imemoryCache 
builder.Services.AddScoped<ICustomMemoryCache, MemoryCache>();

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

app.MapControllers();

app.Run();
