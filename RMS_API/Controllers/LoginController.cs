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
        private readonly IDataHandler _dh;

        public LoginController(IJwtAuth jwtAuth, IDataHandler dataHandler)
        {
            _jwtAuth = jwtAuth;
            _dh = dataHandler;
        }

        // POST: api/Login/UserLogin
        [HttpPost("UserLogin")]
        public IActionResult UserLogin([FromBody] LoginModel br)
        {
            try
            {
                SqlParameter[] param =
                {
                 new SqlParameter("@UserEmail", br.UsernameOrEmail),
                 new SqlParameter("@Password", br.Password),
                };
                var result = _dh.ReadDataWithResponse("Usp_Sys_UserLogin", param);

                return Ok(result);
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);

            }
        }
    }
}
