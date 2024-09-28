using Microsoft.AspNetCore.Authorization;
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
    [Authorize]
    public class MenuController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public MenuController(ApplicationDbContext context)
        {
            _context = context;
        }
        // GET: api/<MenuController>
        [HttpGet("MenuList")]
        public async Task<ActionResult<IEnumerable<CategoryModel>>> MenuList()
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
     
        [HttpGet]
        public async Task<ActionResult<IEnumerable<MenuModel>>> Get()
        {
            try
            {
                var menus = await _context.Menus
                                .Include(m=>m.Category)
                                .Select(m=>new MenuModel
                                {
                                    CategoryId = m.Category.CategoryName,
                                    MenuId = m.MenuId,
                                    MenuName = m.MenuName,
                                    Description = m.Description,
                                    Price = m.Price,
                                    IsAvailable = m.IsAvailable,
                                    GUID = m.GUID
                                })
                                .ToListAsync();
                return Ok(menus);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }
     
        // GET api/<MenuController>/5
        [HttpGet("{id}")]
        public async Task<ActionResult<MenuModel>> Get(int id)
        {
            try
            {

                var menu = await _context.Menus
                             .Include(c => c.Category)  // Includes related Menu items for each Category
                             .Select(m => new MenuModel
                                 {
                                     MenuId = m.MenuId,
                                     CategoryId= m.CategoryId.ToString(),
                                     MenuName = m.MenuName,
                                     Description = m.Description,
                                     Price = m.Price,
                                     IsAvailable = m.IsAvailable,
                                     GUID = m.GUID,
                                     Active = m.Active
                             })
                             .FirstOrDefaultAsync();
                if(menu is not null) { 
                    return Ok(menu);
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
       
        [HttpPost]
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
                    CategoryId =Convert.ToInt32(menu.CategoryId),
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
        [HttpPut]
        public async Task<IActionResult> Put([FromBody] MenuModel menu)
        {
            try
            {
                var id = menu.MenuId;
                var curMenu = await _context.Menus.FindAsync(id);
                if(curMenu == null)
                {
                    return NotFound($"Menu with ID {id} not found.");
                }

                curMenu.MenuName = menu.MenuName;
                curMenu.Description = menu.Description;
                curMenu.Price = menu.Price;
                curMenu.IsAvailable = menu.IsAvailable;
                curMenu.CategoryId = Convert.ToInt32(menu.CategoryId);
                await _context.SaveChangesAsync();
                return Ok(curMenu);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }
        
        [HttpPut("MenuDetails")]
        public async Task<IActionResult> MenuDetails([FromBody] CategoryModel category)
        {
            try
            {
                using (var transaction = await _context.Database.BeginTransactionAsync())
                {
                    try
                    {
                        var id = category.CategoryId;
                        var curCategory = await _context.Categories.FindAsync(id);
                        if (curCategory == null)
                        {
                            return NotFound($"Category with ID {id} not found.");
                        }

                        curCategory.CategoryName = category.CategoryName;
                        curCategory.Active = category.Active ?? true;
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
                                    Active = true,
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
        [HttpDelete("{id}")]
        public ActionResult Delete(int id)
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

       
    }
}
