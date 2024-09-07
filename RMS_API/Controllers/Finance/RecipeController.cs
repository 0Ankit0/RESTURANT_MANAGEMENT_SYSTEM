using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Models.Finance;
using RMS_API.Models.Menu;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace RMS_API.Controllers.Finance
{
    [Route("api/[controller]")]
    [ApiController]
    public class RecipeController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public RecipeController(ApplicationDbContext context)
        {
            _context = context;
        }
        // GET: api/<RecipeController>
        [HttpGet]
        public async Task<ActionResult<IEnumerable<RecipeModel>>> Get()
        {
            try
            {
                var recipes =await _context.Recipes.Include(r => r.Inventory).Include(r => r.Menu).ToListAsync();
                return Ok(recipes);

            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET api/<RecipeController>/5
        [HttpGet("{id}")]
        public async Task<ActionResult<IEnumerable<RecipeModel>>> Get(int id)
        {
            try
            {
                var recipes = await _context.Recipes
                             .Include(r => r.Inventory)
                             .Include(r => r.Menu)
                             .Where(r => r.MenuId == id)
                             .ToListAsync();

                if (recipes == null )
                    return NotFound();

                return Ok(recipes);

            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // POST api/<RecipeController>
        [HttpPost]
        public void Post([FromBody] string value)
        {
        }

        // PUT api/<RecipeController>/5
        [HttpPut("{id}")]
        public void Put(int id, [FromBody] string value)
        {
        }

        // DELETE api/<RecipeController>/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id)
        {
            try
            {
                var recipes = await _context.Recipes
                            .Where(r => r.MenuId == id)
                            .ToListAsync();

                if (!recipes.Any())
                {
                    return NotFound();
                }

                _context.Recipes.RemoveRange(recipes);
                await _context.SaveChangesAsync();

                return Ok("Recipe deleted successfully");

            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");

            }
        }
    }
}
