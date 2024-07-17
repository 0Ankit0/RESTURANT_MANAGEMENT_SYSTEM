using Microsoft.AspNetCore.Authentication.Cookies;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();

//To add Response caching to the application
//check: https://docs.microsoft.com/en-us/aspnet/core/performance/caching/response?view=aspnetcore-8.0 for more details
builder.Services.AddResponseCaching();

//Add authentication scheme to the application
//check: https://docs.microsoft.com/en-us/aspnet/core/security/authentication/cookie?view=aspnetcore-8.0 for more details
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/Login/Index";
        options.AccessDeniedPath = "/Login/Index?accessDenied=true";
    });

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

//To add Response caching middleware
app.UseResponseCaching();

app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}");

app.Run();
