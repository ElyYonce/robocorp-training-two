from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import os

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    open_robot_order_website()
    orders = get_orders()
    close_annoying_modal()
    for order in orders:
        fill_the_form(order)
        preview_the_order()
        submit_the_order(order)
        order_another_robot()
    archive_receipts()


def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite=True)

    tables = Tables()
    table = tables.read_table_from_csv("orders.csv")
    return table

def close_annoying_modal():
    page = browser.page()
    page.get_by_role("button", name="I guess so...").click()

def fill_the_form(order):
    page = browser.page()
    page.get_by_label("Head:").select_option(str(order["Head"]))
    page.get_by_role('radio').nth(int(order["Body"])-1).click()
    page.get_by_role("spinbutton", name="Legs:").fill(str(order["Legs"]))
    page.get_by_role("textbox", name="Shipping address").fill(str(order["Address"]))

def preview_the_order():
    page = browser.page()
    page.get_by_role("button", name="Preview").click()
    robot_image = page.locator("#robot-preview-image")
    robot_image.is_visible()

def submit_the_order(order):
    page = browser.page()
    order_button = page.get_by_role("button", name="Order")
    order_another_button = page.get_by_role("button", name="Order another robot")
    page.get_by_role("button", name="Order").click()
    if order_another_button.is_visible():
        robot_image_path = screenshot_robot(order)
        save_receipt_as_pdf(order, robot_image_path)
        return
    else:
        for i in range(5):
            order_button.click()
            robot_image_path = screenshot_robot(order)
            if order_another_button.is_visible():
                save_receipt_as_pdf(order, robot_image_path)
                break

def order_another_robot():
    page = browser.page()
    page.get_by_role("button", name="Order another robot").click()
    close_annoying_modal()

def save_receipt_as_pdf(order, robot_image_path):
    page = browser.page()
    pdf = PDF()
    
    receipt_window = page.locator("#receipt")
    receipt_pdf_path = f"output/receipts/receipt_{str(order['Order number'])}.pdf"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(receipt_pdf_path), exist_ok=True)
    
    if receipt_window.is_visible():
        try:
            # Get the receipt HTML
            receipt_html = receipt_window.inner_html()
            
            # Create HTML with both receipt and image
            combined_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                    <div style="text-align: center; margin-bottom: 30px; color: #2c3e50;">
                        <h1 style="margin: 0; font-size: 24px; color: #2c3e50;">RobotSpareBin Industries Inc.</h1>
                    </div>
                    
                    <div style="background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px;">
                        {receipt_html}
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <img src="{robot_image_path}" 
                             alt="Robot Preview" 
                             style="display: block; margin: 0 auto; max-width: 400px; height: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 14px;">
                        <p>Thank you for your order!</p>
                    </div>
                </body>
            </html>
            """
            
            # Convert the combined HTML to PDF
            pdf.html_to_pdf(combined_html, receipt_pdf_path)
            
            # Verify PDF was created
            if not os.path.exists(receipt_pdf_path):
                raise Exception(f"Failed to create PDF file at {receipt_pdf_path}")
            
        except Exception as e:
            raise
    else:
        raise Exception("Receipt window is not visible")

def screenshot_robot(order):
    page = browser.page()
    robot_image = page.locator("#robot-preview-image")
    robot_image_path = f"output/robot_images/robot_image_{str(order['Order number'])}.png"
    
    robot_image.is_visible()
    robot_image.screenshot(path=robot_image_path)
    
    # Verify screenshot was created
    if not os.path.exists(robot_image_path):
        raise Exception(f"Failed to create robot screenshot at {robot_image_path}")
        
    return robot_image_path

def archive_receipts():
    receipts_dir = "output/receipts"
    archive_file = "output/receipts.zip"
    
    archive = Archive()
    archive.archive_folder_with_zip(receipts_dir, archive_file, recursive=True)

