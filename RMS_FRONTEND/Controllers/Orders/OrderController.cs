using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Data;
using RMS_FRONTEND.Data.Orders;
using RMS_FRONTEND.Models.Menu;
using RMS_FRONTEND.Models.Orders;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Orders
{
    public class OrderController : Controller
    {
        private readonly DummyDbContext _context;
		private readonly IApiCall _apiCall;

		public OrderController(DummyDbContext context,IApiCall apiCall)
        {
            _context = context;
            _apiCall = apiCall;
        }

        // GET: Order
        public async Task<IActionResult> Index()
        {
			var responseData = await _apiCall.GetAsync("Order");
			var orders = JsonConvert.DeserializeObject<IEnumerable<OrderModel>>(responseData);
			return View(orders);
        }

        // GET: Order/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var orderDetails = await _context.OrderDetails
                .Include(o => o.Menu)
                .Include(o => o.Order)
                .FirstOrDefaultAsync(m => m.OrderDetailId == id);
            if (orderDetails == null)
            {
                return NotFound();
            }

            return View(orderDetails);
        }

        // GET: Order/Create
        public async Task<IActionResult> Create()
        {
            var responseData = await _apiCall.GetAsync("Menu");
            var menus = JsonConvert.DeserializeObject<IEnumerable<MenuModel>>(responseData) ?? Enumerable.Empty<MenuModel>();
            ViewData["MenuId"] = new SelectList(menus, "MenuId", "MenuName");
            return View();
        }

        // POST: Order/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([FromForm] OrderModel order)
        {
            if (ModelState.IsValid)
            {
                var responseData = await _apiCall.PostAsync("Order",order);
                return RedirectToAction(nameof(Index));
            }
           
            return View(order);
        }

        // GET: Order/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var order = await _apiCall.GetAsync("Order", $"{id}");
            var responseData = await _apiCall.GetAsync("Menu");
            var menus = JsonConvert.DeserializeObject<IEnumerable<MenuModel>>(responseData) ?? Enumerable.Empty<MenuModel>();
            ViewData["MenuId"] = new SelectList(menus, "MenuId", "MenuName");
            var orderModel= JsonConvert.DeserializeObject<OrderModel>(order);
            return View(orderModel);
        }

        // POST: Order/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("OrderDetailId,OrderId,MenuId,Quantity,Price")] OrderDetails orderDetails)
        {
            if (id != orderDetails.OrderDetailId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(orderDetails);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!OrderDetailsExists(orderDetails.OrderDetailId))
                    {
                        return NotFound();
                    }
                    else
                    {
                        throw;
                    }
                }
                return RedirectToAction(nameof(Index));
            }
            ViewData["MenuId"] = new SelectList(_context.Menus, "MenuId", "MenuId", orderDetails.MenuId);
            ViewData["OrderId"] = new SelectList(_context.Orders, "OrderId", "OrderId", orderDetails.OrderId);
            return View(orderDetails);
        }

        // GET: Order/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var orderDetails = await _context.OrderDetails
                .Include(o => o.Menu)
                .Include(o => o.Order)
                .FirstOrDefaultAsync(m => m.OrderDetailId == id);
            if (orderDetails == null)
            {
                return NotFound();
            }

            return View(orderDetails);
        }

        // POST: Order/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var orderDetails = await _context.OrderDetails.FindAsync(id);
            if (orderDetails != null)
            {
                _context.OrderDetails.Remove(orderDetails);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool OrderDetailsExists(int id)
        {
            return _context.OrderDetails.Any(e => e.OrderDetailId == id);
        }
    }
}
