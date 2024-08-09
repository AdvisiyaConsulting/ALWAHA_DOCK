# Use the official Odoo image as the base
FROM odoo:15.0

# Set a custom user to run Odoo (optional)
#USER root
# Set the working directory for Odoo addons


# Install additional Python packages
RUN pip install validate_email_address
# Copy your custom addons into the image
COPY ./addons /mnt/extra-addons/custom_addons

# Set the entrypoint script as the entrypoint for the container
CMD ["odoo"]