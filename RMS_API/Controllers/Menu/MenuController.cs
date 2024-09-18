using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Menu;
using RMS_API.Models.Menu;
using RMS_API.Models.Orders;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace RMS_API.Controllers.Menu
{
    [Route("api/[controller]")]
    [ApiController]
    public class MenuController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public MenuController(ApplicationDbContext context)
        {
            _context = context;
        }
        // GET: api/<MenuController>
        [HttpGet]
        public async Task<ActionResult<IEnumerable<CategoryModel>>> Get()
        {
            try
            {
                var categories = await _context.Categories
                             .Include(c => c.Menus)  // Includes related Menu items for each Category
                             .Select(c => new CategoryModel
                             {
                                 CategoryId = c.CategoryId,
                                 CategoryName = c.CategoryName,
                                 GUID = c.GUID,
                                 Active = c.Active,
                                 // Map Menu details for each category
                                 Menu = c.Menus.Select(m => new MenuModel
                                 {
                                     MenuId = m.MenuId,
                                     MenuName = m.MenuName,
                                     Description = m.Description,
                                     Price = m.Price,
                                     IsAvailable = m.IsAvailable,
                                     GUID = m.GUID,
                                     Active = m.Active
                                 }).ToList()
                             })
                             .ToListAsync();
                return Ok(categories);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // GET api/<MenuController>/5
        [HttpGet("{id}")]
        public async Task<ActionResult<IEnumerable<CategoryModel>>> Get(int id)
        {
            try
            {

                var categories = await _context.Categories
                             .Include(c => c.Menus)  // Includes related Menu items for each Category
                             .Where(c => c.CategoryId == id)
                             .Select(c => new CategoryModel
                             {
                                 CategoryId = c.CategoryId,
                                 CategoryName = c.CategoryName,
                                 GUID = c.GUID,
                                 Active = c.Active,
                                 // Map Menu details for each category
                                 Menu = c.Menus.Select(m => new MenuModel
                                 {
                                     MenuId = m.MenuId,
                                     MenuName = m.MenuName,
                                     Description = m.Description,
                                     Price = m.Price,
                                     IsAvailable = m.IsAvailable,
                                     GUID = m.GUID,
                                     Active = m.Active
                                 }).ToList()
                             })
                             .FirstOrDefaultAsync();
                if(categories is not null) { 
                    return Ok(categories);
                }
                else
                {
                    return NotFound();
                }

            }
            catch (Exception ex) {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // POST api/<MenuController>
        [HttpPost("Category")]
        public ActionResult Post([FromBody] CategoryModel category)
        {
            try
            {
                var newCategory = new CategoryMaster
                {
                    CategoryName = category.CategoryName,
                    GUID = Guid.NewGuid().ToString(),
                    Active = true
                };
                _context.Categories.AddAsync(newCategory);
                _context.SaveChanges();
                return Ok(newCategory);
            }catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        [HttpPost("Menu")]
        public ActionResult Post([FromBody] MenuModel menu)
        {
            try
            {
                var newMenu = new MenuMaster
                {
                    MenuName = menu.MenuName,
                    Description = menu.Description,
                    Price = menu.Price,
                    IsAvailable = menu.IsAvailable,
                    CategoryId = menu.CategoryId,
                    GUID = Guid.NewGuid().ToString(),
                    Active = true
                };
                _context.Menus.AddAsync(newMenu);
                _context.SaveChanges();
                return Ok(newMenu);
            }catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // PUT api/<MenuController>/5
        [HttpPut("Menu/{id}")]
        public async Task<IActionResult> Put(int id, [FromBody] MenuModel menu)
        {
            try
            {
                var curMenu = await _context.Menus.FindAsync(id);
                if(curMenu == null)
                {
                    return NotFound($"Menu with ID {id} not found.");
                }

                curMenu.MenuName = menu.MenuName;
                curMenu.Description = menu.Description;
                curMenu.Price = menu.Price;
                curMenu.IsAvailable = menu.IsAvailable;
                curMenu.CategoryId = menu.CategoryId;
                await _context.SaveChangesAsync();
                return Ok(curMenu);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        [HttpPut("Category/{id}")]
        public async Task<IActionResult> Put(int id, [FromBody] CategoryModel category)
        {
            try
            {
                using (var transaction = await _context.Database.BeginTransactionAsync())
                {
                    try
                    {
                        var curCategory = await _context.Categories.FindAsync(id);
                        if (curCategory == null)
                        {
                            return NotFound($"Category with ID {id} not found.");
                        }

                        curCategory.CategoryName = category.CategoryName;
                        curCategory.Active = category.Active;
                        // Handle menu updates
                        // Remove menus that are not in the incoming model
                        var menuIds = category.Menu.Select(m => m.MenuId).ToList();
                        curCategory.Menus.RemoveAll(m => !menuIds.Contains(m.MenuId));

                        // Update or add new menus
                        foreach (var menu in category.Menu)
                        {
                            var existingMenu = curCategory.Menus.FirstOrDefault(m => m.MenuId == menu.MenuId);
                            if (existingMenu != null)
                            {
                                // Update existing menu
                                existingMenu.MenuName = menu.MenuName;
                                existingMenu.Description = menu.Description;
                                existingMenu.Price = menu.Price;
                                existingMenu.IsAvailable = menu.IsAvailable;
                            }
                            else
                            {
                                // Add new menu
                                curCategory.Menus.Add(new MenuMaster
                                {
                                    CategoryId = curCategory.CategoryId,
                                    MenuName = menu.MenuName,
                                    Description = menu.Description,
                                    Price = menu.Price,
                                    IsAvailable = menu.IsAvailable,
                                    Active = menu.Active,
                                    GUID = menu.GUID
                                });
                            }
                        }

                        await _context.SaveChangesAsync();
                        await transaction.CommitAsync();
                        return Ok(curCategory);
                    }
                    catch (Exception ex)
                    {
                        await transaction.RollbackAsync();
                        return StatusCode(500, $"Internal server error: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // DELETE api/<MenuController>/5
        [HttpDelete("Menu/{id}")]
        public ActionResult DeleteMenu(int id)
        {
            try
            {
                var menu = _context.Menus.Find(id);
                if (menu != null)
                {
                    _context.Menus.Remove(menu);
                    _context.SaveChanges();
                    return Ok(menu);
                }
                else
                {
                    return NotFound($"Menu with ID {id} not found.");
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"Error deleting menu with ID {id}: {ex.Message}");
            }
        }

        [HttpDelete("Category/{id}")]
        public ActionResult DeleteCategory(int id)
        {
            try
            {
                var category = _context.Categories.Find(id);
                if (category == null)
                {
                    return NotFound($"Category with ID {id} not found.");
                }

                // Check if any menus are associated with this category
                var associatedMenus = _context.Menus.Any(m => m.CategoryId == id);
                if (associatedMenus)
                {
                    return BadRequest("Category cannot be deleted because it is associated with one or more menus. Please make sure that the category is empty before deleting.");
                }

                // If no associated menus, proceed with deletion
                _context.Categories.Remove(category);
                _context.SaveChanges();
                return Ok($"Category with ID {id} has been successfully deleted.");
            }
            catch (Exception ex)
            {
                // Handle the exception and log it as necessary
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

    }
}
