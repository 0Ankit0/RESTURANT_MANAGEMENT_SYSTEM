using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Finance;
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
        public ActionResult Post([FromBody] RecipeModelWithMenu recipe)
        {
            try
            {
                foreach (var item in recipe.Recipes)
                {
                    Recipe recipemaster = new Recipe
                    {
                        MenuId = recipe.MenuId,
                        InventoryId = item.InventoryId,
                        QuantityRequired = item.QuantityRequired,
                        GUID = Guid.NewGuid().ToString()
                    };

                     _context.Recipes.AddAsync(recipemaster);
                }
                _context.SaveChangesAsync();
                return Ok("Recipe added successfully");
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // PUT api/<RecipeController>/5
        [HttpPut("Recipe/{menuId}")]
        public async Task<IActionResult> Put(int menuId, [FromBody] RecipeModelWithMenu recipeWithMenu)
        {
            using (var transaction = await _context.Database.BeginTransactionAsync())
            {
                try
                {
                    // Retrieve the menu from the database
                    var curMenu = await _context.Menus.Include(m => m.Recipes).FirstOrDefaultAsync(m => m.MenuId == menuId);
                    if (curMenu == null)
                    {
                        return NotFound($"Menu with ID {menuId} not found.");
                    }

                    // Remove recipes that are not in the incoming model
                    var recipeIds = recipeWithMenu.Recipes.Select(r => r.RecipeId).ToList();
                    curMenu.Recipes.RemoveAll(r => !recipeIds.Contains(r.RecipeId));

                    // Update existing recipes or add new ones
                    foreach (var recipe in recipeWithMenu.Recipes)
                    {
                        var existingRecipe = curMenu.Recipes.FirstOrDefault(r => r.RecipeId == recipe.RecipeId);
                        if (existingRecipe != null)
                        {
                            // Update existing recipe
                            existingRecipe.InventoryId = recipe.InventoryId;
                            existingRecipe.QuantityRequired = recipe.QuantityRequired;
                            existingRecipe.GUID = recipe.GUID;
                        }
                        else
                        {
                            // Add new recipe
                            curMenu.Recipes.Add(new Recipe
                            {
                                MenuId = curMenu.MenuId,
                                InventoryId = recipe.InventoryId,
                                QuantityRequired = recipe.QuantityRequired,
                                GUID = recipe.GUID
                            });
                        }
                    }

                    // Save changes and commit the transaction
                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync(); // Commit transaction after successful save

                    return Ok(curMenu);
                }
                catch (Exception ex)
                {
                    await transaction.RollbackAsync(); // Rollback transaction in case of error
                    return StatusCode(500, $"Internal server error: {ex.Message}");
                }
            }
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
