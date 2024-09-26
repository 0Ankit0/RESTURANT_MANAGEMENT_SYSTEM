using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Models.Menu;
using RMS_FRONTEND.Models.Orders;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Orders
{
    public class OrderController : Controller
    {
		private readonly IApiCall _apiCall;

		public OrderController(IApiCall apiCall)
        {
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

            var orderDetails = await _apiCall.GetAsync("Order/", $"{id}");
            var orderModel = JsonConvert.DeserializeObject<OrderModel>(orderDetails);
            return View(orderModel);
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
            var orderModel= JsonConvert.DeserializeObject<OrderWithDetails>(order);
            return View(orderModel);
        }

        // POST: Order/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit([FromForm] OrderWithDetails orders)
        {
            if (ModelState.IsValid)
            {
                var orderModel = await _apiCall.PutAsync("Order", orders);
                return RedirectToAction(nameof(Index));
            }
            return View(orders);
        }

        // GET: Order/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var orderDetails = await _apiCall.DeleteAsync("Order/", $"{id}");
            var orderModel = JsonConvert.DeserializeObject<UserModel>(orderDetails);
            return View(orderModel);
           
        }

        
    }
}
