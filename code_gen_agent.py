import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import google.generativeai as genai
import re
import os
from datetime import datetime
import threading

# Configure API key
API_KEY = "AIzaSyBsLNLyU8pNyUjnNDyvN_JSubGVV0M9yjU"
genai.configure(api_key=API_KEY)

# Initialize the model
model = genai.GenerativeModel('models/gemini-2.5-flash')

class CodeGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Code Generator Chatbot")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")
        
        # Store generated code
        self.generated_code = ""
        self.detected_language = ""
        self.full_code_to_show = ""
        
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg="#2d2d2d", height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 AI Code Generator Chatbot",
            font=("Arial", 18, "bold"),
            bg="#2d2d2d",
            fg="#61dafb"
        )
        title_label.pack(pady=10)
        
        # Chat Display Area
        chat_frame = tk.Frame(self.root, bg="#1e1e1e")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#61dafb",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure tags for styling
        self.chat_display.tag_config("user", foreground="#61dafb", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("bot", foreground="#98c379", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("code", foreground="#e5c07b", font=("Consolas", 9))
        self.chat_display.tag_config("info", foreground="#c678dd", font=("Arial", 9, "italic"))
        
        # Input Frame
        input_frame = tk.Frame(self.root, bg="#1e1e1e")
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.input_box = tk.Text(
            input_frame,
            height=3,
            font=("Arial", 11),
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#61dafb",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_box.bind("<Return>", self.handle_enter)
        
        # Button Frame
        button_frame = tk.Frame(input_frame, bg="#1e1e1e")
        button_frame.pack(side=tk.RIGHT)
        
        self.send_button = tk.Button(
            button_frame,
            text="Send",
            command=self.send_message,
            bg="#61dafb",
            fg="#1e1e1e",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.send_button.pack()
        
        # Action Buttons Frame
        action_frame = tk.Frame(self.root, bg="#1e1e1e")
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.download_button = tk.Button(
            action_frame,
            text="💾 Download Code",
            command=self.download_code,
            bg="#98c379",
            fg="#1e1e1e",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = tk.Button(
            action_frame,
            text="🗑️ Clear Chat",
            command=self.clear_chat,
            bg="#e06c75",
            fg="#1e1e1e",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Welcome message
        self.add_bot_message("Welcome! I'm your AI Code Generator. Ask me to generate any code and I'll create it for you! 🚀")
    
    def handle_enter(self, event):
        if event.state & 0x1:  # Shift+Enter for new line
            return
        else:
            self.send_message()
            return "break"
    
    def add_user_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, "You: ", "user")
        self.chat_display.insert(tk.END, f"{message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def add_bot_message(self, message, tag="bot"):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, "Bot: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def add_code_preview(self, code, language):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, f"📝 Generated Code ({language}):\n", "info")
        
        # Show first 15 lines of code
        code_lines = code.split('\n')
        preview_lines = code_lines[:15]
        preview = '\n'.join(preview_lines)
        
        self.chat_display.insert(tk.END, f"{preview}\n", "code")
        
        if len(code_lines) > 15:
            # Store the full code for this preview
            self.full_code_to_show = code
            
            # Create clickable link
            link_text = f"... ({len(code_lines) - 15} more lines)\n"
            self.chat_display.insert(tk.END, link_text, "clickable")
            
            # Make it look like a link
            self.chat_display.tag_config("clickable", foreground="#61dafb", underline=True)
            self.chat_display.tag_bind("clickable", "<Button-1>", self.show_full_code)
            self.chat_display.tag_bind("clickable", "<Enter>", lambda e: self.chat_display.config(cursor="hand2"))
            self.chat_display.tag_bind("clickable", "<Leave>", lambda e: self.chat_display.config(cursor=""))
        
        self.chat_display.insert(tk.END, "\n✅ Click 'Download Code' button to save the file.\n", "info")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def show_full_code(self, event=None):
        """Show the full code when clicked"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Insert full code after the preview
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.insert(tk.END, "--- Full Code ---\n", "info")
        self.chat_display.insert(tk.END, f"{self.full_code_to_show}\n", "code")
        self.chat_display.insert(tk.END, "--- End of Code ---\n", "info")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def detect_language(self, code):
        """Detect programming language from code"""
        language_patterns = {
            'python': [r'def ', r'import ', r'print\(', r'class .*:', r'from .* import'],
            'java': [r'public class', r'public static void main', r'System\.out\.', r'import java\.'],
            'cpp': [r'#include', r'int main\(', r'std::', r'cout <<', r'using namespace'],
            'c': [r'#include', r'int main\(', r'printf\('],
            'javascript': [r'function ', r'const ', r'let ', r'var ', r'=>', r'console\.log'],
            'html': [r'<!DOCTYPE', r'<html>', r'<body>', r'<div>'],
            'css': [r'\{[\s\S]*?\}', r'@media', r'\.class'],
        }
        
        for lang, patterns in language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    return lang
        
        return 'txt'
    
    def get_file_extension(self, language):
        """Get file extension based on language"""
        extensions = {
            'python': '.py',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c',
            'javascript': '.js',
            'html': '.html',
            'css': '.css',
            'txt': '.txt'
        }
        return extensions.get(language, '.txt')
    
    def generate_code(self, user_query):
        """Generate code based on user query"""
        prompt = f"""You are a code generator. Generate ONLY the executable code for the following request.
Do NOT include any explanations, markdown formatting, code blocks, or additional text.
Return ONLY the raw code that can be directly saved to a file and executed.

User Request: {user_query}

Generate the code now:"""
        
        try:
            response = model.generate_content(prompt)
            code = response.text
            
            # Clean up any markdown code blocks if present
            code = re.sub(r'^```[\w]*\n', '', code)
            code = re.sub(r'\n```$', '', code)
            code = code.strip()
            
            return code, None
        
        except Exception as e:
            return None, f"Error generating code: {str(e)}"
    
    def send_message(self):
        user_message = self.input_box.get("1.0", tk.END).strip()
        
        if not user_message:
            return
        
        # Clear input box
        self.input_box.delete("1.0", tk.END)
        
        # Add user message to chat
        self.add_user_message(user_message)
        
        # Disable send button while generating
        self.send_button.config(state=tk.DISABLED, text="Generating...")
        self.download_button.config(state=tk.DISABLED)
        
        # Generate code in separate thread
        thread = threading.Thread(target=self.generate_and_display, args=(user_message,))
        thread.daemon = True
        thread.start()
    
    def generate_and_display(self, user_message):
        """Generate code and display it"""
        code, error = self.generate_code(user_message)
        
        if error:
            self.root.after(0, lambda: self.add_bot_message(f"❌ {error}"))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL, text="Send"))
        else:
            # Detect language
            language = self.detect_language(code)
            
            # Store generated code
            self.generated_code = code
            self.detected_language = language
            
            # Display code preview
            self.root.after(0, lambda: self.add_code_preview(code, language))
            self.root.after(0, lambda: self.download_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL, text="Send"))
    
    def download_code(self):
        """Download the generated code"""
        if not self.generated_code:
            messagebox.showwarning("No Code", "No code has been generated yet!")
            return
        
        # Get file extension
        extension = self.get_file_extension(self.detected_language)
        
        # Ask user where to save
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[
                (f"{self.detected_language.upper()} files", f"*{extension}"),
                ("All files", "*.*")
            ],
            initialfile=f"generated_code{extension}"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.generated_code)
                
                messagebox.showinfo("Success", f"Code saved successfully to:\n{file_path}")
                self.add_bot_message(f"✅ Code downloaded successfully as: {os.path.basename(file_path)}")
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
    
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Reset generated code
        self.generated_code = ""
        self.detected_language = ""
        self.full_code_to_show = ""  # Add this line
        self.download_button.config(state=tk.DISABLED)
        
        # Show welcome message again
        self.add_bot_message("Chat cleared! Ready for a new code generation request. 🚀")

def main():
    root = tk.Tk()
    app = CodeGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()