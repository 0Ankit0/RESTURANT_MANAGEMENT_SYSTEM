using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using RMS_API.Data;
using RMS_API.Data.Orders;
using StackExchange.Redis;

namespace RMS_API.Controllers.Orders
{
    public class OrderController : Controller
    {
        private readonly ApplicationDbContext _context;

        public OrderController(ApplicationDbContext context)
        {
            _context = context;
        }

        // GET: OrderController
        public ActionResult Index()
        {
            return View();
        }

     // GET: OrderController/Details/5
    public async Task<ActionResult<OrderDetails>> Details(int id)
    {
        try
        {
            var roleMaster =_context.OrderDetails.Where(od => od.OrderId == id).ToList();

            if (roleMaster == null)
            {
                return NotFound($"Order with ID {id} not found.");
            }

            return Ok(roleMaster);
        }
        catch (Exception ex)
        {
            return StatusCode(500, $"Internal server error: {ex.Message}");
        }
    }

        // GET: OrderController/Create
        public ActionResult Create()
        {
            return View();
        }

        // POST: OrderController/Create
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Create(IFormCollection collection)
        {
            try
            {
                return RedirectToAction(nameof(Index));
            }
            catch
            {
                return View();
            }
        }

        // GET: OrderController/Edit/5
        public ActionResult Edit(int id)
        {
            return View();
        }

        // POST: OrderController/Edit/5
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Edit(int id, IFormCollection collection)
        {
            try
            {
                return RedirectToAction(nameof(Index));
            }
            catch
            {
                return View();
            }
        }

        // GET: OrderController/Delete/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id)
        {
            try
            {
                var order = await _context.Orders.FindAsync(id);
                if (order == null)
                {
                    return NotFound($"Order with ID {id} not found.");
                }

                _context.Orders.Remove(order);
                await _context.SaveChangesAsync();

                return Ok("Order has been deleted successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        
    }
}
