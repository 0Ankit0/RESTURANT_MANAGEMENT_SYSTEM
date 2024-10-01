using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.Data;
using RMS_API.Data.Finance;
using RMS_API.Models.Finance;
using RMS_API.Models.Users;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace RMS_API.Controllers.Finance
{
    [Route("api/{version:apiVersion}/[controller]")]
    [ApiController]
    [Authorize]
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

                InventoryTransaction transaction = new InventoryTransaction
                {
                    InventoryId = inventory.InventoryId,
                    TransactionDate = DateTime.Now,
                    Quantity = inventory.Quantity,
                    TransactionType = TransactionType.Addition,
                    Description = "Initial addition"
                };

                _context.InventoryTransactions.Add(transaction);
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
        public async Task<ActionResult> Put(int id, [FromBody] InventoryModel im)
        {
            try
            {
                var inventory = await _context.Inventories.FirstOrDefaultAsync(i => i.InventoryId == id);
                if (inventory == null)
                {
                    return NotFound();
                }

                decimal quantityDifference = im.Quantity - inventory.Quantity;

                inventory.Quantity = im.Quantity;
                inventory.ItemName = im.ItemName;
                inventory.Unit = im.Unit;
                _context.Inventories.Update(inventory);
                await _context.SaveChangesAsync();

                InventoryTransaction transaction = new InventoryTransaction
                {
                    InventoryId = inventory.InventoryId,
                    TransactionDate = DateTime.Now,
                    Quantity = quantityDifference,
                    TransactionType = quantityDifference > 0 ? TransactionType.Addition : TransactionType.Subtraction,
                    Description = "Update inventory"
                };

                _context.InventoryTransactions.Add(transaction);
                await _context.SaveChangesAsync();

                return Ok(inventory);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        [HttpGet("report/total-value")]
        public async Task<ActionResult> GetTotalInventoryValue()
        {
            var totalValue = await _context.Inventories
                .SumAsync(i => i.Quantity * i.Recipes.Sum(r => r.QuantityRequired));

            return Ok(new { TotalValue = totalValue });
        }

        [HttpGet("report/transactions")]
        public async Task<ActionResult> GetInventoryTransactions(DateTime startDate, DateTime endDate)
        {
            var transactions = await _context.InventoryTransactions
                .Where(t => t.TransactionDate >= startDate && t.TransactionDate <= endDate)
                .Select(t => new
                {
                    t.TransactionId,
                    t.InventoryId,
                    t.TransactionDate,
                    t.Quantity,
                    t.TransactionType,
                    t.Description
                })
                .ToListAsync();

            return Ok(transactions);
        }

        [HttpGet("report/low-stock")]
        public async Task<ActionResult> GetLowStockItems(decimal threshold)
        {
            var lowStockItems = await _context.Inventories
                .Where(i => i.Quantity < threshold)
                .Select(i => new
                {
                    i.InventoryId,
                    i.ItemName,
                    i.Quantity,
                    i.Unit
                })
                .ToListAsync();

            return Ok(lowStockItems);
        }

        [HttpGet("report/changes-over-time")]
        public async Task<ActionResult> GetInventoryChangesOverTime(DateTime startDate, DateTime endDate)
        {
            var changes = await _context.InventoryTransactions
                .Where(t => t.TransactionDate >= startDate && t.TransactionDate <= endDate)
                .GroupBy(t => t.TransactionDate.Date)
                .Select(g => new
                {
                    Date = g.Key,
                    TotalChange = g.Sum(t => t.Quantity)
                })
                .ToListAsync();

            return Ok(changes);
        }


        // DELETE api/<InventoryController>/5
        [HttpDelete("{id}")]
        public async Task<ActionResult> Delete(int id)
        {
            try
            {
                var inventory = await _context.Inventories.FirstOrDefaultAsync(i => i.InventoryId == id);
                if (inventory == null)
                {
                    return NotFound();
                }
                _context.Inventories.Remove(inventory);
                await _context.SaveChangesAsync();
                return Ok(inventory);

            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }
    }
}
