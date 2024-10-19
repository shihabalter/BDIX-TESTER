import requests
import concurrent.futures
import os
import sys
from datetime import datetime
import time
import traceback
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

class BDIXTester:
    def __init__(self):
        self.console = Console()
        self.websites = []
        self.working_sites = []
        self.timeout = 5  # Default timeout
        self.bdix_url = "https://raw.githubusercontent.com/shihabalter/BDIX-TESTER/refs/heads/main/bdix.txt"  # URL for bdix.txt

    def set_timeout(self, timeout):
        """Set the timeout value for requests."""
        try:
            self.timeout = float(timeout)
            self.console.print(f"[green]Timeout set to {self.timeout} seconds[/green]")
        except ValueError:
            self.console.print("[red]Invalid timeout value. Using default (5 seconds)[/red]")
            self.timeout = 5

    def download_bdix_file(self):
        """Download the bdix.txt file from the repository."""
        try:
            self.console.print("[yellow]Downloading bdix.txt file...[/yellow]")
            response = requests.get(self.bdix_url, timeout=10)
            response.raise_for_status()
            
            # Get the path for bdix.txt
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            bdix_path = os.path.join(exe_dir, 'bdix.txt')
            
            # Save the file
            with open(bdix_path, 'w', encoding='utf-8') as file:
                file.write(response.text)
            
            self.console.print("[green]Successfully downloaded bdix.txt[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]Error downloading bdix.txt: {str(e)}[/red]")
            return False

    def load_websites(self):
        """Load websites from the local bdix.txt file or download if not present."""
        try:
            # Get the path for bdix.txt
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            bdix_path = os.path.join(exe_dir, 'bdix.txt')
            
            # If file doesn't exist or is empty, try to download it
            if not os.path.exists(bdix_path) or os.path.getsize(bdix_path) == 0:
                if not self.download_bdix_file():
                    return False
            
            # Read the file
            with open(bdix_path, 'r', encoding='utf-8') as file:
                self.websites = [line.strip() for line in file if line.strip()]
            
            if self.websites:
                self.console.print(f"[green]Successfully loaded {len(self.websites)} websites[/green]")
                return True
            
            self.console.print("[red]Error: bdix.txt is empty.[/red]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Error loading websites: {str(e)}[/red]")
            return False

    def test_website(self, url):
        """Test a single website's connectivity."""
        if not url.startswith(('http://', 'https://')):
            url = f'http://{url}'
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return url, True
            return url, False
        except:
            return url, False

    def save_results(self):
        """Save working websites to a file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"working_sites_{timestamp}.txt"
            
            # Save in the same directory as the executable
            if getattr(sys, 'frozen', False):
                filename = os.path.join(os.path.dirname(sys.executable), filename)
            
            with open(filename, 'w', encoding='utf-8') as file:
                for site in self.working_sites:
                    file.write(f"{site}\n")
            
            self.console.print(f"[green]Results saved to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving results: {str(e)}[/red]")

    def run_tests(self):
        """Run the connectivity tests."""
        try:
            self.console.clear()
            self.console.print(Panel.fit(
                Text("BDIX TESTER", justify="center", style="bold white on blue"),
                subtitle="Testing BDIX Connectivity"
            ))

            if not self.websites:
                if self.load_websites():
                    self.console.print("[green]Successfully reloaded websites.[/green]")
                else:
                    self.console.print("[red]No websites loaded. Please check your internet connection.[/red]")
                    return

            self.working_sites = []
            total_sites = len(self.websites)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("[cyan]Testing websites...", total=total_sites)
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_url = {executor.submit(self.test_website, url): url for url in self.websites}
                    
                    for future in concurrent.futures.as_completed(future_to_url):
                        url, is_working = future.result()
                        progress.advance(task)
                        
                        if is_working:
                            self.working_sites.append(url)
                            self.console.print(f"[green]✓ {url} is working[/green]")
                        else:
                            self.console.print(f"[red]✗ {url} is not working[/red]")

            self.console.print("\n[bold]Test Results:[/bold]")
            self.console.print(f"Total sites tested: {total_sites}")
            self.console.print(f"Working sites: {len(self.working_sites)}")
            self.console.print(f"Failed sites: {total_sites - len(self.working_sites)}")
            
        except Exception as e:
            self.console.print(f"[red]Error during testing: {str(e)}[/red]")
            self.console.print(traceback.format_exc())

def main():
    try:
        # Add a small delay to ensure console is ready
        time.sleep(1)
        
        # Create console and show welcome message
        console = Console()
        console.print(Panel.fit(
            Text("Welcome to BDIX TESTER", justify="center", style="bold white on blue"),
            subtitle="Starting up..."
        ))
        
        tester = BDIXTester()
        if not tester.load_websites():
            console.print("[yellow]Attempting to download bdix.txt...[/yellow]")
            if not tester.download_bdix_file() or not tester.load_websites():
                console.print("[red]Failed to initialize. Please check your internet connection.[/red]")
                input("Press Enter to exit...")
                return

        while True:
            print("\n1. Start Testing")
            print("2. Save Working Sites")
            print("3. Set Timeout")
            print("4. Reload BDIX List")
            print("5. Exit")
            
            try:
                choice = input("\nEnter your choice (1-5): ")
            except EOFError:
                choice = '5'
            
            if choice == '1':
                tester.run_tests()
            elif choice == '2':
                if tester.working_sites:
                    tester.save_results()
                else:
                    print("No results to save. Please run the tests first.")
            elif choice == '3':
                timeout = input("Enter timeout in seconds (default is 5): ")
                tester.set_timeout(timeout)
            elif choice == '4':
                if tester.download_bdix_file() and tester.load_websites():
                    print("Successfully reloaded BDIX list.")
                else:
                    print("Failed to reload BDIX list.")
            elif choice == '5':
                print("Thank you for using BDIX Tester!")
                break
            else:
                print("Invalid choice. Please try again.")
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()