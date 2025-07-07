import smtplib, os
from aiosmtplib import SMTP
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader, select_autoescape
import asyncio

# Set up Jinja2 environment pointing to your templates folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_activation_email(activation_link: str) -> str:
    template = env.get_template("activation_email.html")
    return template.render(activation_link=activation_link)


async def send_activation_email(to_email: str, activation_link: str, from_email: str, from_password: str):
    html_content = render_activation_email(activation_link)
    # print(html_content,'-')
    msg = EmailMessage()
    msg["Subject"] = "Activate your account"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content("Please activate your account by visiting the link.")
    msg.add_alternative(html_content, subtype='html')
    
    smtp = SMTP(hostname="smtp.gmail.com", port=587, start_tls=True)
    await smtp.connect()
    await smtp.login(from_email, from_password)
    
    # Send the email: convert message to string
    await smtp.sendmail(from_email, to_email, msg.as_string())
    await smtp.quit() 
    
def send_email(to_email:str, activation_link:str, from_email:str, from_password:str):
    asyncio.run(send_activation_email(to_email=to_email, activation_link=activation_link, from_email=from_email, from_password=from_password))
