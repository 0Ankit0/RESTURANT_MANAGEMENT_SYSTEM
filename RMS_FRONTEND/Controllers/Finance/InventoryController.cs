using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Models.Finance;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Finance
{
    public class InventoryController : Controller
    {
        private readonly IApiCall _apiCall;

        public InventoryController(IApiCall apiCall)
        {
            _apiCall = apiCall;
        }

        // GET: Inventory
        public async Task<IActionResult> Index()
        {
			var responseData = await _apiCall.GetAsync("Inventory");
			var inventories = JsonConvert.DeserializeObject<IEnumerable<InventoryModel>>(responseData);
            return View(inventories);
		}

        // GET: Inventory/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var inventory = await _apiCall.GetAsync("Inventory/", $"{id}");
            var inventoryModel = JsonConvert.DeserializeObject<InventoryModel>(inventory);
            return View(inventoryModel);
        }

        // GET: Inventory/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Inventory/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("ItemName,Quantity,Unit")] InventoryModel inventory)
        {
            if (ModelState.IsValid)
            {
                var inventoryMaster = await _apiCall.PostAsync("Inventory/",inventory);
                var inventoryModel = JsonConvert.DeserializeObject<InventoryModel>(inventoryMaster);
                return View(inventoryModel);
            }
            return View(inventory);
        }

        // GET: Inventory/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var inventoryMaster = await _apiCall.GetAsync("Inventory/", $"{id}");
            var inventoryModel = JsonConvert.DeserializeObject<InventoryModel>(inventoryMaster);
            return View(inventoryModel);
        }

        // POST: Inventory/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("InventoryId,ItemName,Quantity,Unit")] InventoryModel inventory)
        {
            if (id != inventory.InventoryId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                var inventoryMaster = await _apiCall.PutAsync("Inventory/", inventory);
                var inventoryModel = JsonConvert.DeserializeObject<InventoryModel>(inventoryMaster);
                
                return RedirectToAction(nameof(Index));
            }
            return View(inventory);
        }

        // GET: Inventory/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var inventoryMaster = await _apiCall.DeleteAsync("Inventory/", $"{id}");
            var inventoryModel = JsonConvert.DeserializeObject<InventoryModel>(inventoryMaster);
            return RedirectToAction(nameof(Index));
        }

    }
}
