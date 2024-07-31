using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.SqlClient;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
using RMS_API.CustomClass;
using RMS_API.Models;
using System.Data;
using System.Text;

namespace RMS_API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class LoginController : ControllerBase
    {
        private readonly IJwtAuth _jwtAuth;

        public LoginController(IJwtAuth jwtAuth)
        {
            _jwtAuth = jwtAuth;
        }

        // POST: api/Login/UserLogin
        [HttpPost("UserLogin")]
        public IActionResult UserLogin([FromBody] LoginModel br)
        {
            try
            {
                return Ok();
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);

            }
        }
    }
}
