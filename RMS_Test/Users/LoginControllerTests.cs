using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Moq;
using RMS_API.Controllers;
using RMS_API.Data;
using RMS_API.Models;
using RMS_API.Data.Users;
using Xunit;
using RMS_API.CustomClass;

namespace RMS_API.Tests
{
    public class LoginControllerTests
    {
        private readonly Mock<IJwtAuth> _mockJwtAuth;
        private readonly Mock<IDataHandler> _mockDataHandler;
        private readonly ApplicationDbContext _context;

        public LoginControllerTests()
        {
            _mockJwtAuth = new Mock<IJwtAuth>();
            _mockDataHandler = new Mock<IDataHandler>();

            var options = new DbContextOptionsBuilder<ApplicationDbContext>()
                            .UseInMemoryDatabase(databaseName: "TestDatabase")
                            .EnableSensitiveDataLogging()  // Enable sensitive data logging
                            .Options;

            _context = new ApplicationDbContext(options);
        }

        [Fact]
        public void UserLogin_ValidCredentials_ReturnsOkWithToken()
        {
            // Arrange
            var user = new UserMaster
            {
                UserName = "testuser",              // Set UserName
                UserEmail = "test@example.com",
                Password = "password",
                GUID = Guid.NewGuid().ToString()
            };
            _context.UserMasters.Add(user);
            _context.SaveChanges();

            var loginModel = new LoginModel
            {
                UsernameOrEmail = "test@example.com",
                Password = "password"
            };

            _mockJwtAuth.Setup(auth => auth.GenerateToken(It.IsAny<string>(), It.IsAny<string>()))
                        .Returns("fake-jwt-token");

            var controller = new LoginController(_mockJwtAuth.Object, _mockDataHandler.Object, _context);

            // Act
            var result = controller.UserLogin(loginModel) as OkObjectResult;

            // Assert
            Assert.NotNull(result); // Ensure the result is not null
            var response = result.Value as ResponseModel;
            Assert.Equal(200, response.status);

            // Explicitly cast the data to a known type or access the dynamic property carefully
            var tokenData = response.data as dynamic;
            Assert.NotNull(tokenData);
            //Assert.Equal("fake-jwt-token", tokenData.Token);
        }

        [Fact]
        public void UserLogin_InvalidCredentials_ReturnsNotFound()
        {
            // Arrange
            var loginModel = new LoginModel
            {
                UsernameOrEmail = "wrong@example.com",
                Password = "wrongpassword"
            };

            var controller = new LoginController(_mockJwtAuth.Object, _mockDataHandler.Object, _context);

            // Act
            var result = controller.UserLogin(loginModel) as ObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(404, result.StatusCode);
            var response = result.Value as ResponseModel;
            Assert.Equal(204, response.status);
            Assert.Equal("Invalid email or password.", response.message);
        }

        [Fact]
        public void RegisterUser_NewUser_ReturnsSuccess()
        {
            // Arrange
            var registerModel = new RegisterModel
            {
                Username = "testuser",
                Email = "newuser@example.com",
                Password = "password",
                PhoneNumber = "1234567890",
                Role = 1
            };

            var role = new RoleMaster
            {
                RoleId = 1,
                RoleName = "Admin"
            };

            _context.RoleMasters.Add(role);
            _context.SaveChanges();

            var controller = new LoginController(_mockJwtAuth.Object, _mockDataHandler.Object, _context);

            // Act
            var result = controller.RegisterUser(registerModel) as OkObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(200, result.StatusCode);
            Assert.Equal("User registered successfully.", result.Value);
        }

        [Fact]
        public void RegisterUser_ExistingUser_ReturnsConflict()
        {
            // Arrange
            var existingUser = new UserMaster
            {
                UserEmail = "existing@example.com",
                Password = "password",
                UserName = "existinguser"
            };
            _context.UserMasters.Add(existingUser);
            _context.SaveChanges();

            var registerModel = new RegisterModel
            {
                Username = "testuser",
                Email = "existing@example.com",
                Password = "password",
                PhoneNumber = "1234567890",
                Role = 1
            };

            var controller = new LoginController(_mockJwtAuth.Object, _mockDataHandler.Object, _context);

            // Act
            var result = controller.RegisterUser(registerModel) as ObjectResult;

            // Assert
            Assert.NotNull(result);
            Assert.Equal(409, result.StatusCode);
            Assert.Equal("User with this email already exists.", result.Value);
        }

        [Fact]
        public void RegisterUser_InvalidRole_ReturnsBadRequest()
        {
            // Arrange
            var registerModel = new RegisterModel
            {
                Username = "testuser",
                Email = "newuser@example.com",
                Password = "password@123",
                ConfirmPassword = "password@123",
                PhoneNumber = "1234567890",
                Role = 999 // Invalid role, assuming 999 does not exist in the RoleMasters table
            };

            // Mock the database context and create the controller
            var controller = new LoginController(_mockJwtAuth.Object, _mockDataHandler.Object, _context);

            // Act

            var result = controller.RegisterUser(registerModel) as ObjectResult;

            // Assert
            Assert.NotNull(result); // Ensure that the result is not null
            Assert.Equal(400, result.StatusCode); // Assert that the status code is 400 Bad Request
            Assert.Equal("Invalid role specified.", result.Value); // Assert that the returned message matches the expected message
        }

    }
}
