import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
from collections import OrderedDict


class MemorySimulator:
    def __init__(self, root):
        """
        Simülatör arayüzünü ve başlangıç değerlerini ayarlar.
        """
        self.root = root
        self.root.title("SRAM/DRAM Simülatörü")

        # --- Tablo Bellek Ayarları ---
        self.sram_rows, self.sram_cols = 3, 3
        self.sram_capacity = self.sram_rows * self.sram_cols
        self.dram_rows, self.dram_cols = 6, 6

        # --- Gerçekçi Gecikme Değerleri ---
        self.sram_access_delay = 5
        self.dram_access_delay = 50

        # --- Gerçekçi Enerji Değerleri ---
        self.sram_read_energy = 0.5
        self.sram_write_energy = 0.6
        self.dram_read_energy = 2.0
        self.dram_write_energy = 2.2
        self.dram_refresh_energy = 3.0

        # --- DRAM Yenileme Ayarları ---
        self.dram_refresh_interval = 10
        self.total_dram_refresh_energy = 0

        # --- Animasyon Hızı ---
        self.animation_speed = 500 # ms

        # --- Simülasyon Durumu ---
        self.simulation_running = False
        self.input_iterator = None
        self._after_id = None
        self.report_window = None

        # --- Arayüz Elemanları ---
        self.setup_ui()

        # --- Metrikler, Tarihçe ve Görsel Konum Takibi ---
        self.reset_metrics()

        # --- Temiz Kapanma için ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_main_window_close)



        # arayüz elemanları oluşumu----
    def setup_ui(self):
        """
        Kullanıcı arayüzü elemanlarını (kontroller, bellek gridleri, grafik) oluşturur ve yerleştirir.
        """
        # Kontrol Paneli
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(control_frame, text="Verilerin Girişi:").pack(side=tk.LEFT, padx=5)
        self.entry = ttk.Entry(control_frame, width=30)
        self.entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Başlat", command=self.start_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Duraklat", command=self.pause_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Adım", command=self.step_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Sıfırla", command=self.reset_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Raporu Göster", command=self.show_final_report).pack(side=tk.LEFT, padx=5)

        # Hız Kontrol
        speed_frame = ttk.Frame(self.root, padding="10")
        speed_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Label(speed_frame, text="Simulasyon Hızı:").pack(side=tk.LEFT)
        self.speed_scale = ttk.Scale(speed_frame, from_=50, to_=2000, command=self.update_speed)
        self.speed_scale.set(self.animation_speed)
        self.speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.speed_label = ttk.Label(speed_frame, text=f"{int(self.animation_speed)}ms")
        self.speed_label.pack(side=tk.LEFT, padx=5)

        # Bellek Görselleştirme
        self.setup_memory_grids()

        # Grafik Alanı
        self.setup_chart()

        # Durum Çubuğu
        self.status_label = ttk.Label(self.root, text="Hazır", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

    def update_speed(self, val):
        """
        Animasyon hızı ölçeğinden gelen değere göre hızı günceller.
        """
        self.animation_speed = float(val)
        if hasattr(self, 'speed_label') and self.speed_label:
             self.speed_label.config(text=f"{int(val)}ms")

    def setup_memory_grids(self):
        """
        SRAM ve DRAM belleklerini temsil eden gridleri oluşturur.
        """
        sram_frame = ttk.LabelFrame(self.root, text=f"SRAM (Önbellek {self.sram_rows}x{self.sram_cols}) - LRU")
        sram_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.sram_labels = self.create_grid(sram_frame, self.sram_rows, self.sram_cols)

        dram_frame = ttk.LabelFrame(self.root, text=f"DRAM (Ana Bellek {self.dram_rows}x{self.dram_cols})")
        dram_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.dram_labels = self.create_grid(dram_frame, self.dram_rows, self.dram_cols)

    def create_grid(self, parent, rows, cols):
        """
        Belirtilen boyutlarda bir etiket (label) gridi oluşturur.
        """
        labels = []
        for i in range(rows):
            row_labels = []
            for j in range(cols):
                label = tk.Label(parent, text="", width=4, height=2, relief="solid", bg="white", font=('Arial', 10))
                label.grid(row=i, column=j, padx=2, pady=2)
                row_labels.append(label)
            labels.append(row_labels)
        return labels

    
    # setup_chart FONKSİYONU canlı çizgi grafiği için
    

    def setup_chart(self):
        """
        Matplotlib kullanarak canlı performans grafiği ayarlanır
        """
        self.fig, self.ax1 = plt.subplots(figsize=(6, 4))
        self.ax2 = self.ax1.twinx()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.fig.suptitle("Bellek Performansı ve Kullanımı")

        # Sol Y ekseni (Sadece Gecikme)
        self.ax1.set_xlabel("Adım Sayısı")
        self.ax1.set_ylabel("Toplam Gecikme (ns)", color='royalblue') # Etiket güncellendi
        self.ax1.tick_params(axis='y', labelcolor='royalblue')
        self.ax1.grid(True, axis='y')

        # Sağ Y ekseni (Enerji)
        self.ax2.set_ylabel("Enerji Kullanımı(pJ)", color='red')
        self.ax2.tick_params(axis='y', labelcolor='red')
        self.ax2.grid(True, axis='y', linestyle='--')

        # --- Çizgileri oluştur (SADECE GECİKME ve ENERJİ) ---
        self.line_sram_delay, = self.ax1.plot([], [], label='SRAM Gecikme (ns)', color='blue')
        self.line_dram_delay, = self.ax1.plot([], [], label='DRAM Gecikme (ns)', color='darkorange')
        # Erişim çizgileri kaldırıldı
        # self.line_sram_access, = self.ax1.plot([], [], label='SRAM Erişim Sayısı', color='cyan', linestyle='--')
        # self.line_dram_access, = self.ax1.plot([], [], label='DRAM Erişim Sayısı', color='teal', linestyle='--')
        self.line_sram_energy, = self.ax2.plot([], [], label='SRAM Enerji (pJ)', color='cornflowerblue')
        self.line_dram_energy, = self.ax2.plot([], [], label='DRAM Enerji (pJ)', color='orange')

        # --- Legend'ları birleştir (SADECE KALANLAR İÇİN) ---
        lines1, labels1 = self.ax1.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        self.canvas.draw()
    # ================================================================
    # /setup_chart FONKSİYONU
    # ================================================================


    def reset_metrics(self):
        """
        Tüm performans metriklerini, önbelleği ve geçmiş verilerini sıfırlar.
        """
        self.sram_access_count = 0
        self.dram_access_count = 0
        self.sram_write_count = 0
        self.cache = {}
        self.sram_visual_map = OrderedDict()
        self.dram_visual_map = {}
        self.step_count = 0
        self.steps_history = []
        self.sram_cumulative_delay_history = []
        self.dram_cumulative_delay_history = []
        self.sram_cumulative_energy_history = []
        self.dram_cumulative_energy_history = []
        self.dram_refresh_cumulative_energy_history = []
        self.sram_access_history = [] # Rapor için tutuluyor
        self.dram_access_history = [] # Rapor için tutuluyor
        self.total_dram_refresh_energy = 0

    # --- start_simulation, pause_simulation, step_simulation ---

    #-------- HATA YÖNETİMİ ----------#
    def start_simulation(self):
        input_text = self.entry.get().strip().upper()
        if not input_text: messagebox.showwarning("Uyarı", "Lütfen bir metin girin!"); return
        self.reset_simulation(); self.input_iterator = iter(input_text)
        self.simulation_running = True; self.update_status("Simülasyon başlatıldı...")
        self.process_next_char()
    def pause_simulation(self):
        if not self.simulation_running: return
        self.simulation_running = False; self.update_status("Simülasyon duraklatıldı.")
        if self._after_id: self.root.after_cancel(self._after_id); self._after_id = None
    def step_simulation(self):
        if not hasattr(self, 'input_iterator') or self.input_iterator is None:
             input_text = self.entry.get().strip().upper()
             if not input_text: messagebox.showwarning("Uyarı", "Lütfen bir metin girin!"); return
             self.reset_simulation(); self.input_iterator = iter(input_text)
             self.update_status("Adım modunda başla...")
        if self.simulation_running: self.pause_simulation()
        self.process_next_char(single_step=True)

    # --- process_next_char  ---
    def process_next_char(self, single_step=False):
        if not self.simulation_running and not single_step: return
        if self.input_iterator is None: self.update_status("Lütfen önce 'Başlat' veya geçerli bir metinle 'Adım' kullanın."); return
        try:
            char = next(self.input_iterator); self.step_count += 1
            refresh_occurred = False; step_refresh_energy = 0
            if self.step_count > 0 and self.step_count % self.dram_refresh_interval == 0:
                refresh_occurred = True; step_refresh_energy = self.dram_refresh_energy; self.total_dram_refresh_energy += step_refresh_energy
            sram_delay, sram_energy, dram_delay, dram_energy, status_msg = self.process_char(char)
            prev_sram_delay = self.sram_cumulative_delay_history[-1] if self.sram_cumulative_delay_history else 0
            prev_dram_delay = self.dram_cumulative_delay_history[-1] if self.dram_cumulative_delay_history else 0
            prev_sram_energy = self.sram_cumulative_energy_history[-1] if self.sram_cumulative_energy_history else 0
            prev_dram_energy = self.dram_cumulative_energy_history[-1] if self.dram_cumulative_energy_history else 0
            prev_refresh_energy = self.dram_refresh_cumulative_energy_history[-1] if self.dram_refresh_cumulative_energy_history else 0
            self.steps_history.append(self.step_count)
            self.sram_cumulative_delay_history.append(prev_sram_delay + sram_delay)
            self.dram_cumulative_delay_history.append(prev_dram_delay + dram_delay)
            self.sram_cumulative_energy_history.append(prev_sram_energy + sram_energy)
            self.dram_cumulative_energy_history.append(prev_dram_energy + dram_energy)
            self.dram_refresh_cumulative_energy_history.append(prev_refresh_energy + step_refresh_energy)
            self.sram_access_history.append(self.sram_access_count)
            self.dram_access_history.append(self.dram_access_count)
            if refresh_occurred: status_msg += f" | DRAM Refresh (+ J)"
            self.update_status(f"Adım {self.step_count}: {status_msg}")
            self.update_charts() 
            self.root.update_idletasks()
            if self.simulation_running and not single_step:
                self._after_id = self.root.after(int(self.animation_speed), self.process_next_char)
            else:
                self._after_id = None
                if not single_step: self.update_status(f"Adım {self.step_count} sonrası duraklatıldı.")
        except StopIteration:
            self.simulation_running = False; self.update_status(f"Simülasyon tamamlandı! ({self.step_count} adım)")
            self.update_charts()
            if self._after_id: self.root.after_cancel(self._after_id); self._after_id = None
            self.show_final_report()
        except Exception as e:
             self.simulation_running = False; messagebox.showerror("Hata", f"Simülasyon sırasında bir hata oluştu:\n{e}"); self.update_status(f"Hata nedeniyle durduruldu: {e}")
             if self._after_id: self.root.after_cancel(self._after_id); self._after_id = None
             self.update_charts(); import traceback; traceback.print_exc()

    # --- find_empty_cell ---
    def find_empty_cell(self, grid_labels):
        rows = len(grid_labels); cols = len(grid_labels[0]) if rows > 0 else 0
        for r in range(rows):
            if r < len(grid_labels):
                for c in range(cols):
                    if c < len(grid_labels[r]) and grid_labels[r][c].winfo_exists() and grid_labels[r][c].cget('text') == "": return r, c
        return None

    # --- İşlem Çubuğu ---
    def process_char(self, char):
        step_sram_delay, step_sram_energy, step_dram_delay, step_dram_energy = 0, 0, 0, 0
        status_msg = ""; sram_original_bg = "white"; dram_original_bg = "white"
        if char in self.sram_visual_map:
            self.sram_access_count += 1; step_sram_delay = self.sram_access_delay; step_sram_energy = self.sram_read_energy
            sram_row, sram_col = self.sram_visual_map[char]; self.highlight_cell(self.sram_labels, sram_row, sram_col, "lightblue", sram_original_bg)
            self.sram_visual_map.move_to_end(char); status_msg = f"'{char}' SRAM HIT. Gecikme: {step_sram_delay}ns, S-Enerji: {step_sram_energy:.1f}pJ"
        else:
            self.dram_access_count += 1; step_dram_delay = self.dram_access_delay; step_dram_energy = self.dram_read_energy
            if char not in self.dram_visual_map:
                dram_pos = self.find_empty_cell(self.dram_labels)
                if dram_pos is None: raise Exception("DRAM görsel alanı doldu!")
                dram_row, dram_col = dram_pos; self.highlight_cell(self.dram_labels, dram_row, dram_col, "lightgreen", dram_original_bg)
                if dram_row < len(self.dram_labels) and dram_col < len(self.dram_labels[dram_row]) and self.dram_labels[dram_row][dram_col].winfo_exists(): self.dram_labels[dram_row][dram_col].config(text=char)
                self.dram_visual_map[char] = (dram_row, dram_col)
            else:
                 dram_row, dram_col = self.dram_visual_map[char]; self.highlight_cell(self.dram_labels, dram_row, dram_col, "yellow", dram_original_bg)
            removed_char = None
            if len(self.sram_visual_map) >= self.sram_capacity:
                try:
                    lru_char, (lru_row, lru_col) = self.sram_visual_map.popitem(last=False); removed_char = lru_char
                    if lru_row < len(self.sram_labels) and lru_col < len(self.sram_labels[lru_row]) and self.sram_labels[lru_row][lru_col].winfo_exists(): self.sram_labels[lru_row][lru_col].config(text="", bg=sram_original_bg)
                    sram_pos = (lru_row, lru_col)
                except KeyError: raise Exception("SRAM dolu ama LRU öğesi çıkarılamadı!")
            else:
                sram_pos = self.find_empty_cell(self.sram_labels)
                if sram_pos is None: raise Exception("SRAM'de boş hücre bulunamadı (kapasite dolmamışken)!")
            sram_row, sram_col = sram_pos
            if sram_row < len(self.sram_labels) and sram_col < len(self.sram_labels[sram_row]) and self.sram_labels[sram_row][sram_col].winfo_exists():
                 self.sram_labels[sram_row][sram_col].config(text=char); self.highlight_cell(self.sram_labels, sram_row, sram_col, "orange", sram_original_bg)
            self.sram_visual_map[char] = (sram_row, sram_col); self.sram_write_count += 1; step_sram_energy = self.sram_write_energy
            status_msg = f"'{char}' DRAM MISS. "
            if removed_char: status_msg += f"LRU ('{removed_char}') çıkarıldı. "
            status_msg += f"D-Gecikme: {step_dram_delay}ns, D-Enerji: {step_dram_energy:.1f}pJ, S-Enerji: {step_sram_energy:.1f}pJ"
        return step_sram_delay, step_sram_energy, step_dram_delay, step_dram_energy, status_msg

    # --- highlight_cell ---
    def highlight_cell(self, grid_labels, row, col, color, original_bg):
        highlight_duration = max(100, int(self.animation_speed * 0.6))
        if 0 <= row < len(grid_labels) and 0 <= col < len(grid_labels[row]):
             label = grid_labels[row][col]
             if label.winfo_exists():
                 current_bg = label.cget('bg')
                 if current_bg != color:
                     label.config(bg=color)
                     label.after(highlight_duration, lambda lbl=label, orig_bg=original_bg: lbl.config(bg=orig_bg) if lbl.winfo_exists() else None)

    # --- update_status, clear_grids, reset_simulation ---
    def update_status(self, message): self.status_label.config(text=message)
    def clear_grids(self):
        for r in range(self.sram_rows):
            for c in range(self.sram_cols):
                 if r < len(self.sram_labels) and c < len(self.sram_labels[r]) and self.sram_labels[r][c].winfo_exists(): self.sram_labels[r][c].config(text="", bg="white")
        for r in range(self.dram_rows):
            for c in range(self.dram_cols):
                 if r < len(self.dram_labels) and c < len(self.dram_labels[r]) and self.dram_labels[r][c].winfo_exists(): self.dram_labels[r][c].config(text="", bg="white")
    def reset_simulation(self):
        self.simulation_running = False
        if self._after_id: self.root.after_cancel(self._after_id); self._after_id = None
        self.input_iterator = None; self.reset_metrics(); self.clear_grids(); self.update_charts(); self.update_status("Sistem sıfırlandı.")
        if self.report_window is not None and self.report_window.winfo_exists(): self.report_window.destroy(); self.report_window = None

    
    # update_charts FONKSİYONU 
    
    def update_charts(self):
        """Grafiği adım adım verilerle günceller ."""
       
        if not all(hasattr(self, attr) for attr in ['line_sram_delay', 'line_dram_delay', 'line_sram_energy', 'line_dram_energy']):
            print("Uyarı: Gerekli çizgi nesneleri bulunamadı.")
            return
        if not hasattr(self, 'canvas') or not self.canvas_widget.winfo_exists():
             return

        try:
            # Line verilerini güncelle
            self.line_sram_delay.set_data(self.steps_history, self.sram_cumulative_delay_history)
            self.line_dram_delay.set_data(self.steps_history, self.dram_cumulative_delay_history)
            self.line_sram_energy.set_data(self.steps_history, self.sram_cumulative_energy_history)
            self.line_dram_energy.set_data(self.steps_history, self.dram_cumulative_energy_history)

            # Grafik limitlerini otomatik ayarlama
            
            self.ax1.relim()
            self.ax1.autoscale_view(tight=True)
            self.ax2.relim()
            self.ax2.autoscale_view(tight=True)

            # Kanvası çizdir 
            self.canvas.draw()
        except Exception as e:
             print(f"Grafik güncelleme hatası : {e}")
             # Hata durumunda eksenleri sıfırlamayı dene
             try:
                 if hasattr(self, 'ax1'): self.ax1.set_xlim(0,1); self.ax1.set_ylim(0,1)
                 if hasattr(self, 'ax2'): self.ax2.set_ylim(0,1)
                 if hasattr(self, 'canvas'): self.canvas.draw()
             except Exception as e2:
                 print(f"Grafik hata sonrası sıfırlama hatası: {e2}")

    


    # --- show_final_report GÜNCEL (Erişim Sayısı ile) ---
    def show_final_report(self):
        if self.step_count == 0: messagebox.showinfo("Rapor", "Simülasyon henüz çalışmadı veya tamamlanmadı."); return
        if self.report_window is not None and self.report_window.winfo_exists(): self.report_window.lift(); return
        self.report_window = tk.Toplevel(self.root); self.report_window.title("Nihai Performans Raporu"); self.report_window.protocol("WM_DELETE_WINDOW", self.on_report_close)
        final_sram_delay = self.sram_cumulative_delay_history[-1] if self.sram_cumulative_delay_history else 0; final_dram_delay = self.dram_cumulative_delay_history[-1] if self.dram_cumulative_delay_history else 0
        final_sram_energy = self.sram_cumulative_energy_history[-1] if self.sram_cumulative_energy_history else 0; final_dram_energy = self.dram_cumulative_energy_history[-1] if self.dram_cumulative_energy_history else 0
        final_refresh_energy = self.dram_refresh_cumulative_energy_history[-1] if self.dram_refresh_cumulative_energy_history else 0; final_total_dram_energy = final_dram_energy + final_refresh_energy
        final_sram_access = self.sram_access_count; final_dram_access = self.dram_access_count
        try:
            fig, axes = plt.subplots(1, 3, figsize=(18, 6)); fig.suptitle("Bellek Performans Karşılaştırması (Simülasyon Sonu)", fontsize=14)
            axes[0].bar(['SRAM', 'DRAM'], [final_sram_delay, final_dram_delay], color=['blue','goldenrod']); axes[0].set_ylabel("Toplam Birikimli Gecikme (ns)"); axes[0].set_title("Toplam Gecikme")
            max_delay = max(final_sram_delay, final_dram_delay, 1)
            for i, v in enumerate([final_sram_delay, final_dram_delay]): axes[0].text(i, v + 0.01 * max_delay, f"{v:.0f}", ha='center', va='bottom')
            axes[0].set_ylim(bottom=0)
            max_energy_for_scale = max(final_sram_energy, final_total_dram_energy, 1); axes[1].bar(['SRAM', 'DRAM Toplam'], [final_sram_energy, final_total_dram_energy], color=['deepskyblue', 'gold']); axes[1].set_ylabel("Toplam Enerji (pJ)"); axes[1].set_title("Toplam Enerji Tüketimi")
            if final_dram_energy > 0.05 * max_energy_for_scale : axes[1].text(1, final_dram_energy / 2, f"Erişim\n{final_dram_energy:.1f} pJ", ha='center', va='center', color='white', weight='bold', fontsize='x-small')
            if final_refresh_energy > 0.05 * max_energy_for_scale: axes[1].text(1, final_dram_energy + final_refresh_energy / 2, f"Refresh\n{final_refresh_energy:.1f} pJ", ha='center', va='center', color='white', weight='bold', fontsize='x-small')
            axes[1].set_ylim(bottom=0); axes[1].text(0, final_sram_energy + 0.01 * max_energy_for_scale, f"{final_sram_energy:.1f}", ha='center', va='bottom'); axes[1].text(1, final_total_dram_energy + 0.01 * max_energy_for_scale, f"Toplam:{final_total_dram_energy:.1f}", ha='center', va='bottom', fontsize='small')
            axes[2].bar(['SRAM (HIT)', 'DRAM (MISS)'], [final_sram_access, final_dram_access], color=['lightskyblue','khaki']); axes[2].set_ylabel("Toplam Erişim Sayısı"); axes[2].set_title("Erişim Sayısı (HIT/MISS)")
            max_access = max(final_sram_access, final_dram_access, 1)
            for i, v in enumerate([final_sram_access, final_dram_access]): axes[2].text(i, v + 0.01 * max_access, str(v), ha='center', va='bottom')
            axes[2].set_ylim(bottom=0)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            canvas = FigureCanvasTkAgg(fig, master=self.report_window); canvas_widget = canvas.get_tk_widget(); canvas_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10); canvas.draw()
        except Exception as e:
            messagebox.showerror("Rapor Hatası", f"Rapor grafiği oluşturulurken hata oluştu:\n{e}", parent=self.report_window); print(f"Rapor grafiği hatası: {e}"); import traceback; traceback.print_exc()
            if self.report_window and self.report_window.winfo_exists(): self.report_window.destroy(); self.report_window = None

    # --- on_report_close, on_main_window_close ---
    def on_report_close(self):
        if self.report_window:
            try:
                if hasattr(self.report_window, 'winfo_children') and self.report_window.winfo_children():
                     canvas_widget = self.report_window.winfo_children()[0]
                     if hasattr(canvas_widget, 'figure'): plt.close(canvas_widget.figure)
            except Exception as e: print(f"Rapor figürü kapatılırken hata (önemsiz): {e}")
            self.report_window.destroy(); self.report_window = None
            
    def on_main_window_close(self):
        if self._after_id: self.root.after_cancel(self._after_id); self._after_id = None
        self.on_report_close()
        if hasattr(self, 'fig'): plt.close(self.fig)
        self.root.destroy()

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MemorySimulator(root)
    root.mainloop()