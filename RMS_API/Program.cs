
using Microsoft.EntityFrameworkCore;
using RMS_API.Configuration;
using RMS_API.Data;
using RMS_API.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Instantiate the swagger configuration class and Configure services using the instance
var swaggerConfig = new SwaggerConfiguration(builder.Configuration);
swaggerConfig.ConfigureServices(builder.Services);

// Configure Entity Framework Core with SQL Server more info https://learn.microsoft.com/en-us/aspnet/core/data/ef-rp/intro?view=aspnetcore-8.0
builder.Services.AddDbContext<ApplicationDbContext>(options =>
	options.UseSqlServer(builder.Configuration.GetConnectionString("BaseAddress")));



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


// Read the connection string
var BaseAddress = builder.Configuration.GetConnectionString("BaseAddress");

//Add the depencencies configuration

var dependenciesConfig = new DependenciesConfiguration(builder.Configuration);
dependenciesConfig.Configureservices(builder.Services);




// Instantiate the JWT configuration class and Configure services using the instance
var jwtConfig = new JwtConfiguration(builder.Configuration);
jwtConfig.ConfigureServices(builder.Services);

//Add logging
builder.Logging.ClearProviders();
builder.Logging.AddConsole();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
    app.UseSwagger();
    app.UseSwaggerUI(
    options =>
    {
        var descriptions = app.DescribeApiVersions();

        foreach (var description in descriptions)
        {
            try
            {
                options.SwaggerEndpoint($"/swagger/{description.GroupName}/swagger.json", description.GroupName.ToUpperInvariant());
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error creating SwaggerDoc for version {description.GroupName}: {ex}");
            }
        }
    });
}

app.UseHttpsRedirection();

//To use authentication
app.UseAuthentication();

app.UseAuthorization();

app.UseCors();

app.MapControllers();

app.MapHub<MessageHub>("/messagehub");

app.Run();
