import os
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# Secret key for simple authentication
SECRET_KEY = "your_secret_key"

# Nginx config file path
NGINX_CONF_PATH = "/etc/nginx/stream.d/vps_stream.conf"

# Function to authenticate API requests
def check_auth(secret_key):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            token = request.headers.get('Authorization')
            if token != secret_key:
                return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Function to check if Nginx map block exists and create it if missing
def ensure_nginx_setup():
    try:
        # Check if the configuration file exists
        if not os.path.exists(NGINX_CONF_PATH):
            with open(NGINX_CONF_PATH, "w") as conf_file:
                conf_file.write("""
                stream {
                    # Map block for dynamically routing subdomains to VPS
                    map $host $backend {
                        default 127.0.0.1;  # Default backend in case of unknown subdomain
                    }

                    server {
                        listen 0.0.0.0:0;  # Listen on all TCP ports
                        server_name *.domain.com;  # Wildcard subdomain

                        proxy_pass $backend;
                        proxy_protocol on;
                    }

                    server {
                        listen 0.0.0.0:0 udp;  # Listen on all UDP ports
                        server_name *.domain.com;

                        proxy_pass $backend;
                        proxy_protocol on;
                    }
                }
                """)
            return False  # Indicates that the config was just created
        return True
    except IOError as e:
        return jsonify({"error": f"Failed to set up Nginx: {str(e)}"}), 500

# Function to add VPS to Nginx map block
def add_vps_to_nginx(subdomain, internal_ip):
    try:
        with open(NGINX_CONF_PATH, "r") as conf_file:
            conf_content = conf_file.read()

        # Check if the subdomain is already in the map block
        if f"{subdomain} " in conf_content:
            return jsonify({"message": "Subdomain is already configured"}), 200

        # Insert the subdomain mapping into the map block
        updated_conf = conf_content.replace(
            "default 127.0.0.1;",
            f"default 127.0.0.1;\n        {subdomain} {internal_ip};"
        )

        # Write the updated configuration back to the file
        with open(NGINX_CONF_PATH, "w") as conf_file:
            conf_file.write(updated_conf)

        return True
    except IOError as e:
        return jsonify({"error": f"Failed to update Nginx config: {str(e)}"}), 500

# Function to remove VPS from Nginx map block
def remove_vps_from_nginx(subdomain):
    try:
        with open(NGINX_CONF_PATH, "r") as conf_file:
            conf_content = conf_file.readlines()

        # Filter out the line corresponding to the subdomain
        updated_conf = [line for line in conf_content if f"{subdomain} " not in line]

        # Write the updated configuration back to the file
        with open(NGINX_CONF_PATH, "w") as conf_file:
            conf_file.writelines(updated_conf)

        return True
    except IOError as e:
        return jsonify({"error": f"Failed to update Nginx config: {str(e)}"}), 500

# Function to reload Nginx after config changes
def reload_nginx():
    nginx_reload = os.system("sudo systemctl reload nginx")
    if nginx_reload != 0:
        return jsonify({"error": "Failed to reload Nginx"}), 500
    return True

# Route to add a VPS to the Nginx configuration
@app.route("/add_vps", methods=["POST"])
@check_auth(SECRET_KEY)
def add_vps():
    subdomain = request.json.get("subdomain")
    internal_ip = request.json.get("internal_ip")

    if not subdomain or not internal_ip:
        return jsonify({"error": "Missing parameters"}), 400

    # Ensure Nginx setup is correct before adding VPS
    nginx_ready = ensure_nginx_setup()
    if not nginx_ready:
        # If the config was just created, reload Nginx to apply the new setup
        reload_status = reload_nginx()
        if reload_status is not True:
            return reload_status

    # Add VPS entry to the Nginx map block
    update_status = add_vps_to_nginx(subdomain, internal_ip)
    if update_status is not True:
        return update_status

    # Reload Nginx to apply changes
    reload_status = reload_nginx()
    if reload_status is not True:
        return reload_status

    return jsonify({"message": "VPS configuration added and Nginx reloaded successfully"}), 200

# Route to remove a VPS from the Nginx configuration
@app.route("/remove_vps", methods=["POST"])
@check_auth(SECRET_KEY)
def remove_vps():
    subdomain = request.json.get("subdomain")

    if not subdomain:
        return jsonify({"error": "Missing parameters"}), 400

    # Ensure Nginx setup is correct before removing VPS
    nginx_ready = ensure_nginx_setup()
    if not nginx_ready:
        return jsonify({"error": "Nginx configuration not set up properly"}), 500

    # Remove VPS entry from the Nginx map block
    update_status = remove_vps_from_nginx(subdomain)
    if update_status is not True:
        return update_status

    # Reload Nginx to apply changes
    reload_status = reload_nginx()
    if reload_status is not True:
        return reload_status

    return jsonify({"message": "VPS configuration removed and Nginx reloaded successfully"}), 200

# Simple home route to check if the server is running
@app.route("/")
def home():
    return jsonify({"message": "API is running!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
