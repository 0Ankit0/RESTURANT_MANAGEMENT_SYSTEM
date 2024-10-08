﻿using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Menu;
using RMS_API.Models.Menu;
using Swashbuckle.AspNetCore.Annotations;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace RMS_API.Controllers.Menu
{
    [Route("api/{version:apiVersion}/[controller]")]
    [ApiController]
    [Authorize]
    public class CategoryController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public CategoryController(ApplicationDbContext context)
        {
            _context = context;
        }
       
        // GET: api/<CategoryController>
        [HttpGet]
        [SwaggerOperation(Summary = "Get all Categories", Description = "Retrieves a list of all Categories.")]
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
                             })
                             .ToListAsync();
                return Ok(categories);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }


        // GET api/<CategoryController>/5
        [HttpGet("{id}")]
        public async Task<ActionResult<IEnumerable<CategoryModel>>> Get(int id)
        {
            try
            {
                var categories = await _context.Categories
                             .Include(c => c.Menus)  // Includes related Menu items for each Category
                              .Where(c=>c.CategoryId==id)
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
                return Ok(categories);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }


        // POST api/<CategoryController>
        [HttpPost]
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
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }


        // PUT api/<CategoryController>/5
        [HttpPut]
        public IActionResult Put([Bind("CategoryId, CategoryName")] CategoryModel category)
        {
            try
            {
                var id = category.CategoryId;
                var curCategory = _context.Categories.Find(id);
                curCategory.CategoryName = category.CategoryName;


                _context.SaveChanges();

                return Ok("User updated successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);
            }
        }


        // DELETE api/<CategoryController>/5
        [HttpDelete("{id}")]
        public ActionResult Delete(int id)
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
