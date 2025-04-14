#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinici.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()



# Okay, deploying a Django app locally within a pharmacy network for free is definitely achievable, but it requires careful setup and understanding the limitations, especially regarding the database and reliability.

# Let's break down the scenarios and the best free solutions:

# **Critical First Step: Replace SQLite**

# SQLite is fantastic for development and single-user desktop apps, but it's **not suitable** for multi-user web applications, even on a local network. It handles concurrent writes poorly and can easily lead to database locks and errors when multiple people try to use the app simultaneously.

# **Your best FREE replacement options:**

# 1.  **PostgreSQL:** Highly recommended for Django. It's robust, feature-rich, open-source, and handles concurrency very well.
# 2.  **MySQL/MariaDB:** Also excellent, widely used, open-source, and good choices. MariaDB is a community-driven fork of MySQL.

# You'll need to install one of these database servers on the computer that will host the application/database. You'll also need to:
# *   Install the appropriate Python database adapter (`psycopg2-binary` for PostgreSQL, `mysqlclient` for MySQL).
# *   Change your Django `settings.py` to use the new database engine, name, user, password, host, and port.
# *   Run `python manage.py migrate` again against the new database to create the schema. You'll likely need to export data from SQLite and import it into the new database if you have existing important data.

# ---

# **Scenario 1: Works on Only One Computer**

# This is the simplest scenario. The computer running the app is the only one that can access it.

# *   **Concept:** Run the database server and the Django application directly on the single pharmacy computer that needs access.
# *   **Database:** Install PostgreSQL or MySQL/MariaDB directly on this computer. Configure Django to connect to it using `HOST = 'localhost'` or `HOST = '127.0.0.1'`.
# *   **Web Server:** You **cannot** use the Django development server (`manage.py runserver`) for anything beyond testing. You need a production-ready WSGI server.
#     *   **Waitress (Good for Windows/Simplicity):** A pure-Python production WSGI server. Easy to install (`pip install waitress`) and run.
#     *   **Gunicorn (Good for Linux/macOS):** Very popular and robust WSGI server. Often used with Nginx, but for single-computer access, Gunicorn alone is sufficient.
# *   **Deployment Steps (Simplified):**
#     1.  Install Python on the target computer.
#     2.  Install PostgreSQL/MySQL on the same computer. Create a database and user for your app.
#     3.  Clone your project from GitHub.
#     4.  Set up a virtual environment (`python -m venv venv`, `source venv/bin/activate` or `venv\Scripts\activate`).
#     5.  Install requirements (`pip install -r requirements.txt`). Include `waitress` or `gunicorn` and the database adapter.
#     6.  Configure `settings.py`:
#         *   `DEBUG = False` (Crucial for security and performance!)
#         *   `ALLOWED_HOSTS = ['localhost', '127.0.0.1']`
#         *   Update `DATABASES` settings for PostgreSQL/MySQL.
#         *   Set a strong `SECRET_KEY`.
#     7.  Run migrations: `python manage.py migrate`
#     8.  Collect static files: `python manage.py collectstatic`
#     9.  Run the WSGI server:
#         *   Waitress: `waitress-serve --listen=127.0.0.1:8000 your_project_name.wsgi:application`
#         *   Gunicorn: `gunicorn --bind 127.0.0.1:8000 your_project_name.wsgi:application`
#     10. Access the app via `http://localhost:8000` or `http://127.0.0.1:8000` in the browser *on that computer only*.
# *   **Pros:** Relatively simple setup, uses existing hardware, software is free.
# *   **Cons:** Only accessible on one machine, requires that machine to be running, relies entirely on that single machine's health, requires manual process management (starting the server) unless you set up a service/scheduled task.

# ---

# **Scenario 2: Works on Multiple Computers (Up to 5) on the Local Network**

# This requires one computer to act as a "server" within the pharmacy's Local Area Network (LAN).

# *   **Concept:** One computer (the "server") runs the database and the Django application (via a WSGI server). Other computers on the same network access it via their web browsers using the server computer's local IP address.
# *   **"Server" Machine:** Choose one reliable computer in the pharmacy. This doesn't need to be a dedicated server machine initially; it could be a reliable desktop PC that is usually turned on during working hours. A dedicated machine (even an older PC repurposed) is better for reliability.
# *   **Database:** Install PostgreSQL or MySQL/MariaDB on the "server" machine. Configure it to accept connections from other computers on the local network (this involves changing firewall rules and database configuration like `listen_addresses` in `postgresql.conf` or `bind-address` in MySQL config).
# *   **Web Server:** Use Waitress or Gunicorn on the "server" machine, but configure it to listen on the network interface, not just localhost.
# *   **Deployment Steps (on the "Server" Machine):**
#     1.  Follow steps 1-5 from Scenario 1 on the chosen "server" machine.
#     2.  Find the local IP address of the "server" machine (e.g., `192.168.1.105`). This is how other computers will find it. (Use `ipconfig` on Windows or `ip addr` on Linux).
#     3.  Configure `settings.py`:
#         *   `DEBUG = False`
#         *   `ALLOWED_HOSTS = ['server_ip_address']` (e.g., `ALLOWED_HOSTS = ['192.168.1.105']`). You might also add its hostname if DNS is set up locally.
#         *   Update `DATABASES` settings. The `HOST` should be the server's IP address or `localhost` if the database is running on the same machine. Ensure the database user has permissions to connect from other hosts on the LAN if needed (though usually the app connects locally to the DB).
#         *   Set a strong `SECRET_KEY`.
#     4.  Run migrations: `python manage.py migrate`
#     5.  Collect static files: `python manage.py collectstatic`
#     6.  Configure the Firewall on the "server" machine to allow incoming connections on the port you'll use (e.g., port 8000) from other computers on the local network.
#     7.  Run the WSGI server, binding to `0.0.0.0` (all available network interfaces) or the specific LAN IP address:
#         *   Waitress: `waitress-serve --listen=*:8000 your_project_name.wsgi:application` (or `--listen=192.168.1.105:8000`)
#         *   Gunicorn: `gunicorn --bind 0.0.0.0:8000 your_project_name.wsgi:application` (or `--bind 192.168.1.105:8000`)
#     8.  **Access from other computers:** Open a web browser on any other computer on the *same network* and go to `http://server_ip_address:8000` (e.g., `http://192.168.1.105:8000`).
# *   **Pros:** Allows multi-user access within the pharmacy, leverages existing network, software is free.
# *   **Cons:** Requires one machine to be a reliable "server," needs basic network configuration (IP addresses, firewall), performance depends on the server machine's specs, relies on the local network being stable, still requires manual process management or setting up a service.

# ---

# **Best Free Solution Overall (for up to 5 users locally):**

# **Scenario 2 (Local Network Server) using PostgreSQL and Gunicorn/Waitress.**

# *   **Database:** PostgreSQL installed on the designated "server" PC.
# *   **WSGI Server:** Gunicorn (if the server PC runs Linux/macOS) or Waitress (if it runs Windows or for simplicity).
# *   **Hosting:** Run everything on one chosen, reliable PC within the pharmacy's LAN.
# *   **Key Configuration:**
#     *   Use PostgreSQL, not SQLite.
#     *   Set `DEBUG = False`.
#     *   Configure `ALLOWED_HOSTS` correctly with the server PC's LAN IP address.
#     *   Bind the WSGI server to `0.0.0.0` or the specific LAN IP and the desired port (e.g., 8000).
#     *   Configure the server PC's firewall to allow incoming connections on that port from the LAN.
#     *   Ensure the server PC is reliably powered on during working hours.

# **Crucial Considerations for ANY Local Deployment:**

# 1.  **Backups:** This is **NON-NEGOTIABLE**. Set up automated daily backups of your PostgreSQL/MySQL database. Store these backups on a different machine or external drive. Losing pharmacy data is a disaster. PostgreSQL has tools like `pg_dump`.
# 2.  **Updates & Security:** Keep the operating system, Python, Django, database server, and all dependencies updated with security patches. Since it holds potentially sensitive pharmacy data, security is paramount even on a local network. Ensure `DEBUG=False` is set!
# 3.  **Reliability:** If the "server" PC crashes, is turned off, or has issues, the application is down for everyone. Consider the reliability of the chosen machine.
# 4.  **Process Management:** Simply running `gunicorn ...` or `waitress-serve ...` in a terminal means it stops when the terminal closes or the user logs out. You'll need to run it as a background service:
#     *   **Linux:** Use `systemd` or `supervisor`.
#     *   **Windows:** Use Task Scheduler or tools like NSSM (Non-Sucking Service Manager).
# 5.  **Data Sensitivity:** Be aware of data privacy regulations (like HIPAA in the US or GDPR in Europe) even for local deployments. Ensure your application handles sensitive data securely.

# This local deployment approach is free in terms of software cost but requires technical effort for setup, maintenance, backups, and ensuring reliability.



# Okay, this is a crucial point for usability! If you're handing this application over to someone non-technical, they absolutely *cannot* be expected to open a command prompt, navigate directories, activate virtual environments, and type `gunicorn --bind ...` or `waitress-serve ...`.

# Here's how it would look and what needs to be done to make it user-friendly:

# **The Goal:** The user needs a simple, ideally one-click (or even zero-click) way to start the application engine and then access it via their web browser.

# **Hiding the Complexity (What the Developer Sets Up):**

# You, the developer, need to package the "run" command into something easy for the end-user. The WSGI server (Waitress or Gunicorn) is still running under the hood, but the user doesn't interact with it directly.

# Here are the common approaches, from simplest to most robust:

# **Option 1: The Simple Script (Double-Click Icon)**

# *   **What the Developer Does:**
#     1.  Create a simple script file (e.g., `.bat` on Windows, `.sh` on Linux/macOS) in the main project folder or on the user's Desktop.
#     2.  This script contains *all* the commands needed to start the server:
#         *   Navigate to the project directory (`cd C:\path\to\pharmacy_app`).
#         *   Activate the virtual environment (`.\venv\Scripts\activate` on Windows or `source venv/bin/activate` on Linux/macOS).
#         *   Run the WSGI server command (`waitress-serve --listen=0.0.0.0:8000 pharmacy_project.wsgi:application` or the Gunicorn equivalent).
#         *   (Optional, Windows `.bat`): Add a `pause` command at the end so the window stays open and the user can see if errors occurred.
#     3.  Give the script a friendly name, like `Start Pharmacy App.bat`.
#     4.  Maybe create a Shortcut to this script on the Desktop with a nice icon.
# *   **What the Non-Tech User Does:**
#     1.  **Finds the Icon:** They see an icon on their Desktop or in a folder labelled "Pharmacy App" called something like "Start Pharmacy App".
#     2.  **Double-Clicks:** They double-click this icon.
#     3.  **Sees a Window (Maybe):** A command window (often black) might pop up. It might show some text indicating the server is starting. *Crucially, this window needs to stay open for the app to keep working.* (This is a downside of the simple script method).
#     4.  **Opens Browser:** They open their usual web browser (Chrome, Firefox, Edge).
#     5.  **Goes to Address:** They type in the application's address (which you provide them, e.g., `http://localhost:8000` if it's running on their own machine, or `http://192.168.1.105:8000` if accessing a central server PC). You should help them bookmark this address!
#     6.  **Uses the App:** The pharmacy system loads in their browser.
#     7.  **To Stop (Less Ideal):** They would typically close the command window that opened when they double-clicked the icon.

# **Option 2: The Background Service (Starts Automatically - The Best UX)**

# *   **What the Developer Does (More Involved Setup):**
#     1.  Configure the WSGI server (Waitress/Gunicorn) and the Django application to run as a background service or daemon on the "server" computer.
#     2.  **Windows:** Use tools like NSSM (Non-Sucking Service Manager) to turn the `waitress-serve` command into a proper Windows Service. This service can be set to start automatically when Windows boots up.
#     3.  **Linux:** Create a `systemd` service file that defines how to start Gunicorn (or Waitress), manage its process, and ensure it starts on boot.
#     4.  Ensure the database (PostgreSQL/MySQL) is also configured to start automatically as a service (this is usually the default when you install them).
# *   **What the Non-Tech User Does:**
#     1.  **Turns on Computer:** They turn on the computer designated as the server (or their own computer, if it's the single-user setup).
#     2.  **Waits a Moment:** The pharmacy application engine (WSGI server + Django) starts automatically in the background. They see *nothing* indicating it's starting (no command window).
#     3.  **Opens Browser:** They open their web browser.
#     4.  **Goes to Address:** They go to the bookmarked address (`http://localhost:8000` or `http://server-ip:8000`).
#     5.  **Uses the App:** The pharmacy system loads.
#     6.  **To Stop:** They don't need to do anything specific to stop the app; it keeps running until the computer is shut down. If there's a problem, they might just need to restart the computer.

# **Summary for the Non-Tech User:**

# *   **WSGI/Gunicorn/Waitress?** They likely **never** hear these terms. You might call it the "Application Engine" or "Server Component" if you need to refer to it.
# *   **How to Start?**
#     *   *Ideally (Service Method):* "You don't have to do anything. Just turn on the computer, wait a minute, and open the pharmacy system bookmark in your browser."
#     *   *Alternatively (Script Method):* "Double-click the 'Start Pharmacy App' icon on your desktop. A black window will appear – just minimize it or leave it open. Then open the pharmacy system bookmark in your browser."
# *   **How to Use?** "Open your web browser (Chrome/Edge/Firefox) and go to [App Address - provide and bookmark this!]".

# The key is abstracting away the technical command-line execution into either a simple clickable script or, preferably, an automatically starting background service. The service method provides a much smoother and more professional experience for the end-user.