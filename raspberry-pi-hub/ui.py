"""
GUI interface for Alpaca Price Hub using tkinter.
Provides screens for credential entry, asset selection, and status monitoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from datetime import datetime
from typing import Dict, List
import threading

import config
from db import Database
from alpaca_client import AlpacaClient
from scheduler import PriceScheduler

logger = logging.getLogger(__name__)


class PriceHubGUI:
    """Main GUI application for Alpaca Price Hub."""

    def __init__(self, db: Database, alpaca_client: AlpacaClient, scheduler: PriceScheduler):
        """
        Initialize the GUI application.

        Args:
            db: Database instance
            alpaca_client: AlpacaClient instance
            scheduler: PriceScheduler instance
        """
        self.db = db
        self.alpaca_client = alpaca_client
        self.scheduler = scheduler

        # Available assets cache
        self.available_assets = {
            'stocks': [],
            'forex': [],
            'crypto': []
        }

        # Current selections
        self.selected_assets = {
            'stocks': set(),
            'forex': set(),
            'crypto': set()
        }

        # Create main window
        self.root = tk.Tk()
        self.root.title("Alpaca Price Hub")
        self.root.geometry("800x600")

        # Check if credentials exist
        api_key, api_secret = self.db.get_credentials()
        if api_key and api_secret:
            # Credentials exist, verify them
            self.alpaca_client.set_credentials(api_key, api_secret)
            success, message = self.alpaca_client.verify_credentials()
            if success:
                self.show_main_screen()
            else:
                self.show_credentials_screen()
        else:
            self.show_credentials_screen()

    def show_credentials_screen(self):
        """Display the credentials input screen."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create frame
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(frame, text="Alpaca API Credentials", font=('Arial', 16, 'bold'))
        title.pack(pady=20)

        # Instructions
        instructions = ttk.Label(
            frame,
            text="Enter your Alpaca API credentials for free-tier market data access.",
            wraplength=600
        )
        instructions.pack(pady=10)

        # API Key field
        ttk.Label(frame, text="API Key ID:").pack(anchor=tk.W, padx=50, pady=(20, 5))
        self.api_key_entry = ttk.Entry(frame, width=50)
        self.api_key_entry.pack(padx=50)

        # API Secret field
        ttk.Label(frame, text="API Secret Key:").pack(anchor=tk.W, padx=50, pady=(20, 5))
        self.api_secret_entry = ttk.Entry(frame, width=50, show="*")
        self.api_secret_entry.pack(padx=50)

        # Status label
        self.cred_status_label = ttk.Label(frame, text="", foreground="blue")
        self.cred_status_label.pack(pady=20)

        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        # Verify button
        verify_btn = ttk.Button(
            button_frame,
            text="Save & Verify",
            command=self.verify_credentials
        )
        verify_btn.pack()

    def verify_credentials(self):
        """Verify the entered credentials."""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showerror("Error", "Please enter both API Key and Secret")
            return

        # Update status
        self.cred_status_label.config(text="Verifying credentials...", foreground="blue")
        self.root.update()

        # Set credentials and verify
        self.alpaca_client.set_credentials(api_key, api_secret)
        success, message = self.alpaca_client.verify_credentials()

        if success:
            # Save credentials
            self.db.save_credentials(api_key, api_secret)
            self.cred_status_label.config(text="✓ " + message, foreground="green")
            self.root.update()

            # Wait a moment then show main screen
            self.root.after(1000, self.show_main_screen)
        else:
            self.cred_status_label.config(text="✗ " + message, foreground="red")
            messagebox.showerror("Verification Failed", message)

    def show_main_screen(self):
        """Display the main asset selection and status screen."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Asset selection tab
        selection_frame = ttk.Frame(notebook, padding="10")
        notebook.add(selection_frame, text="Asset Selection")
        self.create_selection_tab(selection_frame)

        # Status tab
        status_frame = ttk.Frame(notebook, padding="10")
        notebook.add(status_frame, text="Status & Prices")
        self.create_status_tab(status_frame)

        # Load existing selections
        self.load_selected_assets()

        # Load available assets
        self.refresh_available_assets()

    def create_selection_tab(self, parent):
        """Create the asset selection tab content."""
        # Title
        title = ttk.Label(parent, text="Select Assets to Track", font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Instructions
        instructions = ttk.Label(
            parent,
            text=f"Select up to {config.MAX_ASSETS_PER_CLASS} assets per class. Use Ctrl+Click to select multiple.",
            wraplength=700
        )
        instructions.pack(pady=5)

        # Create three columns for asset classes
        columns_frame = ttk.Frame(parent)
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Stocks column
        self.create_asset_column(columns_frame, "Stocks", 'stocks', 0)

        # Forex column
        self.create_asset_column(columns_frame, "Forex", 'forex', 1)

        # Crypto column
        self.create_asset_column(columns_frame, "Crypto", 'crypto', 2)

        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20)

        # Refresh button
        refresh_btn = ttk.Button(
            button_frame,
            text="Refresh Asset Lists",
            command=self.refresh_available_assets
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Save button
        save_btn = ttk.Button(
            button_frame,
            text="Save Selections & Start Updates",
            command=self.save_selections
        )
        save_btn.pack(side=tk.LEFT, padx=5)

    def create_asset_column(self, parent, title, asset_class, column):
        """Create a column for selecting assets of a specific class."""
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.grid(row=0, column=column, padx=10, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Count label
        count_label = ttk.Label(frame, text=f"Selected: 0/{config.MAX_ASSETS_PER_CLASS}")
        count_label.pack()

        # Listbox with scrollbar
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=scrollbar.set,
            height=15
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Store references
        setattr(self, f'{asset_class}_listbox', listbox)
        setattr(self, f'{asset_class}_count_label', count_label)

        # Bind selection change
        listbox.bind('<<ListboxSelect>>', lambda e: self.on_selection_change(asset_class))

        # Clear button
        clear_btn = ttk.Button(
            frame,
            text="Clear Selection",
            command=lambda: self.clear_selection(asset_class)
        )
        clear_btn.pack(pady=5)

    def refresh_available_assets(self):
        """Fetch available assets from Alpaca and populate listboxes."""
        # Show loading message
        logger.info("Fetching available assets from Alpaca...")

        # Run in separate thread to avoid blocking GUI
        def fetch_assets():
            try:
                # Fetch stocks
                stocks = self.alpaca_client.get_stock_assets()
                self.available_assets['stocks'] = stocks
                self.root.after(0, lambda: self.populate_listbox('stocks', stocks))

                # Fetch forex
                forex = self.alpaca_client.get_forex_assets()
                self.available_assets['forex'] = forex
                self.root.after(0, lambda: self.populate_listbox('forex', forex))

                # Fetch crypto
                crypto = self.alpaca_client.get_crypto_assets()
                self.available_assets['crypto'] = crypto
                self.root.after(0, lambda: self.populate_listbox('crypto', crypto))

                logger.info("Asset lists refreshed successfully")

            except Exception as e:
                logger.error(f"Error fetching assets: {e}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to fetch assets: {str(e)}"
                ))

        thread = threading.Thread(target=fetch_assets, daemon=True)
        thread.start()

    def populate_listbox(self, asset_class, assets):
        """Populate a listbox with available assets."""
        listbox = getattr(self, f'{asset_class}_listbox')
        listbox.delete(0, tk.END)

        for asset in assets:
            symbol = asset['symbol']
            name = asset.get('name', symbol)
            display = f"{symbol} - {name}" if name != symbol else symbol
            listbox.insert(tk.END, display)

            # Re-select if previously selected
            if symbol in self.selected_assets[asset_class]:
                listbox.selection_set(listbox.size() - 1)

    def on_selection_change(self, asset_class):
        """Handle selection changes in listboxes."""
        listbox = getattr(self, f'{asset_class}_listbox')
        count_label = getattr(self, f'{asset_class}_count_label')

        # Get current selections
        selected_indices = listbox.curselection()
        selected_count = len(selected_indices)

        # Check if exceeds max
        if selected_count > config.MAX_ASSETS_PER_CLASS:
            messagebox.showwarning(
                "Selection Limit",
                f"You can only select up to {config.MAX_ASSETS_PER_CLASS} {asset_class}"
            )
            # Deselect the last one
            listbox.selection_clear(selected_indices[-1])
            selected_count -= 1

        # Update count label
        count_label.config(text=f"Selected: {selected_count}/{config.MAX_ASSETS_PER_CLASS}")

    def clear_selection(self, asset_class):
        """Clear all selections for an asset class."""
        listbox = getattr(self, f'{asset_class}_listbox')
        listbox.selection_clear(0, tk.END)
        self.on_selection_change(asset_class)

    def load_selected_assets(self):
        """Load previously selected assets from database."""
        for asset_class in ['stocks', 'forex', 'crypto']:
            selected = self.db.get_selected_assets(asset_class)
            self.selected_assets[asset_class] = {asset['symbol'] for asset in selected}

    def save_selections(self):
        """Save selected assets to database and start scheduler."""
        try:
            # Clear existing selections
            self.db.clear_selected_assets()

            # Save new selections
            for asset_class in ['stocks', 'forex', 'crypto']:
                listbox = getattr(self, f'{asset_class}_listbox')
                selected_indices = listbox.curselection()

                for idx in selected_indices:
                    display_text = listbox.get(idx)
                    # Extract symbol (before " - " if present)
                    symbol = display_text.split(' - ')[0].strip()
                    self.db.add_selected_asset(symbol, asset_class)

            # Start scheduler if not already running
            if not self.scheduler.is_running:
                self.scheduler.start()

            messagebox.showinfo(
                "Success",
                "Asset selections saved!\n\n"
                f"Price updates will run every {config.UPDATE_INTERVAL_MINUTES} minutes.\n"
                "Check the Status tab for details."
            )

            logger.info("Asset selections saved and scheduler started")

        except Exception as e:
            logger.error(f"Error saving selections: {e}")
            messagebox.showerror("Error", f"Failed to save selections: {str(e)}")

    def create_status_tab(self, parent):
        """Create the status and price display tab."""
        # Title
        title = ttk.Label(parent, text="Scheduler Status & Latest Prices", font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Scheduler Status", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=10)

        self.status_text = ttk.Label(status_frame, text="Initializing...", font=('Arial', 10))
        self.status_text.pack()

        # Refresh button
        refresh_btn = ttk.Button(
            status_frame,
            text="Refresh Status",
            command=self.update_status_display
        )
        refresh_btn.pack(pady=5)

        # Prices display
        prices_frame = ttk.LabelFrame(parent, text="Latest Prices", padding="10")
        prices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrolled text widget for prices
        self.prices_display = scrolledtext.ScrolledText(
            prices_frame,
            height=20,
            font=('Courier', 9)
        )
        self.prices_display.pack(fill=tk.BOTH, expand=True)

        # Auto-update status every 10 seconds
        self.update_status_display()
        self.schedule_status_update()

    def schedule_status_update(self):
        """Schedule periodic status updates."""
        self.update_status_display()
        self.root.after(10000, self.schedule_status_update)  # Every 10 seconds

    def update_status_display(self):
        """Update the status display with current scheduler info and prices."""
        try:
            # Get scheduler status
            status = self.scheduler.get_status()

            status_text = f"Scheduler: {'Running ✓' if status['is_running'] else 'Stopped ✗'}\n"
            if status['last_update']:
                last_update = datetime.fromisoformat(status['last_update'])
                status_text += f"Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if status['next_update']:
                next_update = datetime.fromisoformat(status['next_update'])
                status_text += f"Next Update: {next_update.strftime('%Y-%m-%d %H:%M:%S')}\n"
            status_text += f"Update Interval: {status['interval_minutes']} minutes"

            self.status_text.config(text=status_text)

            # Update prices display
            self.update_prices_display()

        except Exception as e:
            logger.error(f"Error updating status: {e}")

    def update_prices_display(self):
        """Update the prices display with latest data."""
        try:
            # Get latest prices
            prices = self.db.get_latest_prices()

            if not prices:
                self.prices_display.delete(1.0, tk.END)
                self.prices_display.insert(tk.END, "No price data available yet.\n\nSelect assets and wait for the first update.")
                return

            # Clear display
            self.prices_display.delete(1.0, tk.END)

            # Header
            header = f"{'Symbol':<12} {'Class':<8} {'PrevCls':<10} {'Open':<10} {'Last':<10} {'Change':<12} {'%':<8} Updated\n"
            header += "-" * 110 + "\n"
            self.prices_display.insert(tk.END, header)

            # Sort by asset class and symbol
            prices.sort(key=lambda x: (x['asset_class'], x['symbol']))

            # Display each asset
            for price in prices:
                symbol = price['symbol']
                asset_class = price['asset_class']
                prev_close = price.get('prev_close') or 0
                open_price = price['open_price'] or 0
                last_price = price['last_price'] or 0
                change_amt = price['change_amount']
                change_pct = price['change_percent']
                updated = price.get('last_updated', 'N/A')

                # Format timestamp
                if updated != 'N/A':
                    try:
                        dt = datetime.fromisoformat(updated)
                        updated = dt.strftime('%H:%M:%S')
                    except:
                        pass

                # Color code based on change
                line = f"{symbol:<12} {asset_class:<8} {prev_close:<10.2f} {open_price:<10.2f} {last_price:<10.2f} "
                line += f"{change_amt:<+12.4f} {change_pct:<+8.2f} {updated}\n"

                self.prices_display.insert(tk.END, line)

        except Exception as e:
            logger.error(f"Error updating prices display: {e}")
            self.prices_display.delete(1.0, tk.END)
            self.prices_display.insert(tk.END, f"Error loading prices: {str(e)}")

    def run(self):
        """Start the GUI main loop."""
        logger.info("Starting GUI")
        self.root.mainloop()

    def close(self):
        """Clean up and close the application."""
        logger.info("Closing application")
        self.scheduler.stop()
        self.root.destroy()
