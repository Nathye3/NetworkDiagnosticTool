import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import socket

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas

from network_tools import ping, ping_latency, dns_lookup, check_port
from health_engine import calculate_health_score

# ======================
# GLOBAL
# ======================
latency_history = []
latest_report = ""
auto_monitoring = False

# ======================
# LATENCY QUALITY
# ======================
def latency_quality(latency):
    if latency is None:
        return "UNKNOWN", "#95a5a6"
    latency = float(latency)
    if latency < 50:
        return "EXCELLENT", "#27ae60"
    elif latency < 100:
        return "GOOD", "#f39c12"
    elif latency < 200:
        return "FAIR", "#e67e22"
    else:
        return "POOR", "#c0392b"

# ======================
# ANALYZE
# ======================
def analyze_network():
    global latest_report

    host = entry_host.get().strip()
    port = entry_port.get().strip()

    if not host:
        messagebox.showerror("Error", "Host wajib diisi")
        return

    progress.start()
    root.update()

    try:
        socket.gethostbyname(host)
    except socket.gaierror:
        progress.stop()
        messagebox.showerror("Error", "Domain tidak valid")
        return

    ping_ok = ping(host)
    latency = ping_latency(host)
    dns_ip = dns_lookup(host)
    port_ok = check_port(host, int(port)) if port.isdigit() else False

    progress.stop()

    if latency:
        latency_history.append(float(latency))
        latency_history[:] = latency_history[-10:]

    update_chart()

    score, status = calculate_health_score(
        ping_ok,
        dns_ip is not None,
        port_ok
    )

    quality, q_color = latency_quality(latency)

    # Update status cards with colors
    if status == "HEALTHY":
        status_label.config(text=status, fg="#27ae60")
    elif status == "DEGRADED":
        status_label.config(text=status, fg="#f39c12")
    else:
        status_label.config(text=status, fg="#c0392b")
    
    score_label.config(text=f"{score}/100")
    latency_label.config(text=quality, fg=q_color)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    latest_report = (
        "AUTO NETWORK MONITORING REPORT\n"
        f"Generated at : {now}\n"
        "=" * 50 + "\n\n"
        f"Target Host        : {host}\n"
        f"Ping Status        : {'✓ OK' if ping_ok else '✗ FAILED'}\n"
        f"Ping Latency       : {latency + ' ms' if latency else 'N/A'}\n"
        f"Latency Quality    : {quality}\n"
        f"DNS Resolution     : {dns_ip if dns_ip else '✗ FAILED'}\n"
        f"Port Status        : {'✓ OPEN' if port_ok else '✗ CLOSED'}\n\n"
        f"Health Score       : {score}/100\n"
        f"Network Condition  : {status}\n"
    )

    output.configure(state="normal")
    output.delete("1.0", tk.END)
    output.insert(tk.END, latest_report)
    output.configure(state="disabled")

# ======================
# AUTO MONITOR
# ======================
def start_auto():
    global auto_monitoring
    auto_monitoring = True
    btn_auto.config(state="disabled")
    btn_stop.config(state="normal")
    auto_loop()

def stop_auto():
    global auto_monitoring
    auto_monitoring = False
    btn_auto.config(state="normal")
    btn_stop.config(state="disabled")

def auto_loop():
    if auto_monitoring:
        analyze_network()
        root.after(5000, auto_loop)

# ======================
# EXPORT PDF
# ======================
def export_report():
    if not latest_report:
        messagebox.showwarning("Warning", "Belum ada report")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF File", "*.pdf")]
    )

    if not file_path:
        return

    c = pdf_canvas.Canvas(file_path, pagesize=A4)
    y = 800
    for line in latest_report.split("\n"):
        c.drawString(40, y, line)
        y -= 14
        if y < 40:
            c.showPage()
            y = 800
    c.save()
    messagebox.showinfo("Success", f"Report berhasil disimpan di:\n{file_path}")

# ======================
# CHART
# ======================
def update_chart():
    ax.clear()
    if latency_history:
        ax.plot(latency_history, marker="o", linewidth=2, markersize=6, 
                color="#3498db", markerfacecolor="#e74c3c")
        ax.fill_between(range(len(latency_history)), latency_history, alpha=0.3, color="#3498db")
    ax.set_title("Latency History", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel("Latency (ms)", fontsize=10)
    ax.set_xlabel("Request #", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_facecolor("#f8f9fa")
    canvas.draw()

# ======================
# UI ROOT
# ======================
root = tk.Tk()
root.title("Auto Network Monitoring Tool")
root.geometry("1300x750")
root.configure(bg="#f5f6fa")

# Style configuration
style = ttk.Style()
style.theme_use('clam')

# Button styles
style.configure("Action.TButton", 
                padding=8, 
                font=("Segoe UI", 9, "bold"))

style.configure("Auto.TButton",
                padding=8,
                font=("Segoe UI", 9, "bold"),
                background="#27ae60")

style.configure("Stop.TButton",
                padding=8,
                font=("Segoe UI", 9, "bold"),
                background="#e74c3c")

# Entry style
style.configure("Custom.TEntry",
                padding=8,
                font=("Segoe UI", 10))

# ======================
# HEADER
# ======================
header = tk.Frame(root, bg="#2c3e50", height=80)
header.pack(fill="x")
header.pack_propagate(False)

header_label = tk.Label(
    header,
    text="🌐 AUTO NETWORK MONITORING",
    font=("Segoe UI", 24, "bold"),
    bg="#2c3e50",
    fg="white"
)
header_label.pack(pady=20)

# ======================
# INPUT SECTION
# ======================
input_section = tk.Frame(root, bg="#ffffff", height=100)
input_section.pack(fill="x", padx=20, pady=15)
input_section.pack_propagate(False)

# Input container
input_container = tk.Frame(input_section, bg="#ffffff")
input_container.pack(expand=True)

# Host input
host_frame = tk.Frame(input_container, bg="#ffffff")
host_frame.pack(side="left", padx=10)
tk.Label(host_frame, text="Target Host", bg="#ffffff", 
         font=("Segoe UI", 9), fg="#7f8c8d").pack(anchor="w")
entry_host = ttk.Entry(host_frame, width=35, style="Custom.TEntry")
entry_host.insert(0, "google.com")
entry_host.pack()

# Port input
port_frame = tk.Frame(input_container, bg="#ffffff")
port_frame.pack(side="left", padx=10)
tk.Label(port_frame, text="Port", bg="#ffffff", 
         font=("Segoe UI", 9), fg="#7f8c8d").pack(anchor="w")
entry_port = ttk.Entry(port_frame, width=12, style="Custom.TEntry")
entry_port.insert(0, "80")
entry_port.pack()

# Buttons
btn_frame = tk.Frame(input_container, bg="#ffffff")
btn_frame.pack(side="left", padx=20)
tk.Label(btn_frame, text="Actions", bg="#ffffff", 
         font=("Segoe UI", 9), fg="#7f8c8d").pack(anchor="w")

btn_container = tk.Frame(btn_frame, bg="#ffffff")
btn_container.pack()

ttk.Button(btn_container, text="🔍 Analyze", 
           command=analyze_network, 
           style="Action.TButton").pack(side="left", padx=3)

btn_auto = ttk.Button(btn_container, text="▶ Auto", 
                      command=start_auto, 
                      style="Auto.TButton")
btn_auto.pack(side="left", padx=3)

btn_stop = ttk.Button(btn_container, text="⏹ Stop", 
                      command=stop_auto, 
                      style="Stop.TButton",
                      state="disabled")
btn_stop.pack(side="left", padx=3)

ttk.Button(btn_container, text="📄 Export PDF", 
           command=export_report,
           style="Action.TButton").pack(side="left", padx=3)

# Progress bar
progress = ttk.Progressbar(root, mode="indeterminate")
progress.pack(fill="x", padx=20)

# ======================
# INFO CARDS
# ======================
cards_section = tk.Frame(root, bg="#f5f6fa")
cards_section.pack(pady=15)

def create_card(parent, title, icon):
    card_frame = tk.Frame(parent, bg="#ffffff", width=280, height=120, 
                         relief="flat", bd=0)
    card_frame.pack(side="left", padx=12)
    card_frame.pack_propagate(False)
    
    # Add subtle shadow effect with border
    card_frame.config(highlightbackground="#dfe6e9", highlightthickness=1)
    
    # Icon and title
    top_frame = tk.Frame(card_frame, bg="#ffffff")
    top_frame.pack(fill="x", padx=15, pady=(15, 5))
    
    tk.Label(top_frame, text=icon, bg="#ffffff", 
             font=("Segoe UI", 18)).pack(side="left")
    tk.Label(top_frame, text=title, bg="#ffffff", 
             font=("Segoe UI", 10, "bold"), fg="#7f8c8d").pack(side="left", padx=10)
    
    # Value label
    value_label = tk.Label(card_frame, text="-", bg="#ffffff", 
                          font=("Segoe UI", 22, "bold"), fg="#2c3e50")
    value_label.pack(expand=True)
    
    return value_label

status_label = create_card(cards_section, "NETWORK STATUS", "📊")
score_label = create_card(cards_section, "HEALTH SCORE", "💯")
latency_label = create_card(cards_section, "LATENCY QUALITY", "⚡")

# ======================
# CONTENT AREA
# ======================
content = tk.Frame(root, bg="#f5f6fa")
content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# Left panel - Report output
left_panel = tk.Frame(content, bg="#ffffff", relief="flat", bd=0)
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
left_panel.config(highlightbackground="#dfe6e9", highlightthickness=1)

report_header = tk.Label(left_panel, text="📋 Report Output", 
                        bg="#ffffff", font=("Segoe UI", 11, "bold"),
                        fg="#2c3e50", anchor="w")
report_header.pack(fill="x", padx=15, pady=(15, 10))

output = tk.Text(
    left_panel,
    font=("Consolas", 10),
    state="disabled",
    bg="#f8f9fa",
    relief="flat",
    padx=15,
    pady=10,
    wrap="word"
)
output.pack(fill="both", expand=True, padx=15, pady=(0, 15))

# Right panel - Chart
right_panel = tk.Frame(content, bg="#ffffff", relief="flat", bd=0)
right_panel.pack(side="right", fill="both", expand=True)
right_panel.config(highlightbackground="#dfe6e9", highlightthickness=1)

chart_header = tk.Label(right_panel, text="📈 Latency Monitoring", 
                       bg="#ffffff", font=("Segoe UI", 11, "bold"),
                       fg="#2c3e50", anchor="w")
chart_header.pack(fill="x", padx=15, pady=(15, 10))

# Create matplotlib chart with better styling
fig, ax = plt.subplots(figsize=(6, 4.5), facecolor='white')
fig.tight_layout(pad=3)

canvas = FigureCanvasTkAgg(fig, master=right_panel)
canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 15))

# Initialize chart
update_chart()

# ======================
# FOOTER
# ======================
footer = tk.Label(
    root,
    text="Network Monitoring Tool v2.0 | Powered by Python",
    font=("Segoe UI", 8),
    bg="#ecf0f1",
    fg="#7f8c8d",
    pady=8
)
footer.pack(fill="x")

root.mainloop()