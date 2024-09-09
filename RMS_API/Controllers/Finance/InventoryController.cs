using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Finance;
using RMS_API.Models.Finance;
using RMS_API.Models.Users;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace RMS_API.Controllers.Finance
{
    [Route("api/[controller]")]
    [ApiController]
    public class InventoryController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public InventoryController(ApplicationDbContext context)
        {
            _context = context;
        }
        // GET: api/<InventoryController>
        [HttpGet]
        public async Task<ActionResult<IEnumerable<InventoryModel>>> Get()
        {
            try
            {
                var inventory = await _context.Inventories.Select(
                    i => new InventoryModel
                    {
                        InventoryId = i.InventoryId,
                        ItemName = i.ItemName,
                        Unit = i.Unit,
                        Quantity = i.Quantity,
                        
                    }).
                    ToListAsync();
                return Ok(inventory);

            }catch(Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");

            }
        }

        // GET api/<InventoryController>/5
        [HttpGet("{id}")]
        public async Task<ActionResult<IEnumerable<InventoryModel>>> Get(int id)
        {
            try
            {
                var inventory = await _context.Inventories
                    .Where(i => i.InventoryId == id)
                    .Select(i => new InventoryModel
                    {
                        InventoryId = i.InventoryId,
                        ItemName = i.ItemName,
                        Unit = i.Unit,
                        Quantity = i.Quantity,
                    }).ToListAsync();
                return Ok(inventory);

            }catch(Exception ex) {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // POST api/<InventoryController>
        [HttpPost]
        public async Task<ActionResult> Post([FromBody] InventoryModel inventoryModel)
        {
            try
            {
                Inventory inventory = new Inventory
                {
                    ItemName = inventoryModel.ItemName,
                    Unit = inventoryModel.Unit,
                    Quantity = inventoryModel.Quantity,
                    GUID = Guid.NewGuid().ToString(),
                    CreatedAt = DateTime.Now
                    
                };
                _context.Inventories.Add(inventory);
                await _context.SaveChangesAsync();
                return Ok(inventory);

            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        // PUT api/<InventoryController>/5
        [HttpPut("{id}")]
        public void Put(int id, [FromBody] string value)
        {
        }

        // DELETE api/<InventoryController>/5
        [HttpDelete("{id}")]
        public void Delete(int id)
        {
        }
    }
}
