import os
import streamlit as st
import json
from datetime import datetime
import report
# Thử tải từ dotenv nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Nếu không có dotenv, bỏ qua

# Import từ các module khác
from question_manager import manage_questions
from surveyhandler import survey_form
from stats_dashboard import stats_dashboard
from admin_dashboard import admin_dashboard
from database_helper import (
    get_supabase_client, 
    check_supabase_config, 
    get_user, 
    register_user, 
    check_email_exists
)
from PIL import Image, UnidentifiedImageError

           
# ------------ Cấu hình logo 2×3 cm ~ 76×113 px ------------
LOGO_WIDTH, LOGO_HEIGHT = 150, 150
SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "gif")

# Đường dẫn thư mục chứa logo
LOGO_DIR = "assets/logos"  # Thư mục chứa logo

# Tạo thư mục logo nếu chưa tồn tại
def ensure_logo_directory():
    """Đảm bảo thư mục logo tồn tại"""
    if not os.path.exists(LOGO_DIR):
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
            print(f"Đã tạo thư mục {LOGO_DIR}")
        except Exception as e:
            st.error(f"Không thể tạo thư mục logo: {e}")
            print(f"Lỗi: {e}")

# Lưu logo được tải lên
def save_uploaded_logo(logo_file, index):
    """Lưu logo đã tải lên vào thư mục"""
    ensure_logo_directory()
    try:
        file_extension = logo_file.name.split('.')[-1].lower()
        if file_extension not in SUPPORTED_FORMATS:
            return False, f"Định dạng không được hỗ trợ: {file_extension}"
        
        file_path = os.path.join(LOGO_DIR, f"logo{index}.{file_extension}")
        with open(file_path, "wb") as f:
            f.write(logo_file.getbuffer())
        return True, file_path
    except Exception as e:
        return False, str(e)

# Tìm tất cả logo đã lưu
def find_saved_logos():
    """Tìm các logo đã lưu trong thư mục"""
    ensure_logo_directory()
    logo_paths = []
    
    # Tìm kiếm file logo1.*, logo2.*, logo3.*
    for i in range(1, 4):
        for ext in SUPPORTED_FORMATS:
            pattern = f"logo{i}.{ext}"
            path = os.path.join(LOGO_DIR, pattern)
            if os.path.exists(path):
                logo_paths.append(path)
                break
    
    return logo_paths

def display_logos():
    """Cho phép tải lên 03 logo và hiển thị chúng cố định trên giao diện."""
    # Tạo container cho logo ở đầu trang
    logo_container = st.container()
    with logo_container:
        col1, col2, col3 = st.columns(3)
        
        # Tìm kiếm logo đã lưu
        saved_logos = find_saved_logos()
        
        # Hiển thị các logo đã lưu
        for i, logo_path in enumerate(saved_logos):
            try:
                if i == 0:
                    with col1:
                        st.image(logo_path, width=LOGO_WIDTH)
                elif i == 1:
                    with col2:
                        st.image(logo_path, width=LOGO_WIDTH)
                elif i == 2:
                    with col3:
                        st.image(logo_path, width=LOGO_WIDTH)
            except Exception as e:
                st.error(f"Lỗi khi hiển thị logo {logo_path}: {e}")
        
        # Hiển thị tiêu đề ứng dụng ở giữa
        st.title("TUV NORD ISO 50001:2018 INTERNAL AUDIT TRAINING COURSE - APP")
    
    # Phần tải lên logo mới - ẩn trong expander để không chiếm nhiều không gian
    with st.expander("Cấu hình logo"):
        st.write("Tải lên 03 logo để hiển thị trên ứng dụng. Logo sẽ được lưu lại cho các lần sử dụng sau.")
        
        col1, col2, col3 = st.columns(3)
        
        # Tạo file uploader cho 3 logo
        with col1:
            logo1 = st.file_uploader("Logo 1", type=SUPPORTED_FORMATS, key="file1")
            if logo1:
                success, msg = save_uploaded_logo(logo1, 1)
                if success:
                    st.success("Đã lưu Logo 1")
                else:
                    st.error(f"Lỗi khi lưu Logo 1: {msg}")
        
        with col2:
            logo2 = st.file_uploader("Logo 2", type=SUPPORTED_FORMATS, key="file2")
            if logo2:
                success, msg = save_uploaded_logo(logo2, 2)
                if success:
                    st.success("Đã lưu Logo 2")
                else:
                    st.error(f"Lỗi khi lưu Logo 2: {msg}")
        
        with col3:
            logo3 = st.file_uploader("Logo 3", type=SUPPORTED_FORMATS, key="file3")
            if logo3:
                success, msg = save_uploaded_logo(logo3, 3)
                if success:
                    st.success("Đã lưu Logo 3")
                else:
                    st.error(f"Lỗi khi lưu Logo 3: {msg}")
        
        # Nếu có logo mới được tải lên, tải lại trang để hiển thị
        if logo1 or logo2 or logo3:
            if st.button("Cập nhật hiển thị logo"):
                st.rerun()

def login_register_form():
    """Hiển thị form đăng nhập và đăng ký"""
    # Kiểm tra xem đã chọn tab nào
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "login"
    
    # Tabs cho đăng nhập và đăng ký
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
    
    # Tab đăng nhập
    with tab1:
        with st.form("login_form"):
            st.subheader("Đăng nhập")
            email = st.text_input("Email", placeholder="Nhập email của bạn")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            
            submit_button = st.form_submit_button("Đăng nhập")
            
            if submit_button:
                if not email or not password:
                    st.error("Vui lòng nhập email và mật khẩu!")
                else:
                    # Xác thực người dùng với Supabase
                    user_info = get_user(email, password)
                    
                    if user_info:
                        st.session_state.user_role = user_info.get("role", "student")
                        st.session_state.user_info = {
                            "email": user_info.get("email", email),
                            "full_name": user_info.get("full_name", "Học viên"),
                            "class_name": user_info.get("class", "Lớp đào tạo")
                        }
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Email hoặc mật khẩu không đúng!")
    
    # Tab đăng ký
    with tab2:
        with st.form("registration_form"):
            st.subheader("Đăng ký tài khoản mới")
            reg_email = st.text_input("Email", placeholder="Nhập email của bạn", key="reg_email")
            reg_password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu", key="reg_password")
            confirm_password = st.text_input("Nhập lại mật khẩu", type="password", placeholder="Xác nhận mật khẩu")
            full_name = st.text_input("Họ và tên", placeholder="Nhập họ và tên đầy đủ")
            class_name = st.text_input("Lớp", placeholder="Nhập tên lớp/khóa học")
            
            register_button = st.form_submit_button("Đăng ký")
            
            if register_button:
                # Kiểm tra các trường thông tin
                if not reg_email or not reg_password or not confirm_password or not full_name:
                    st.error("Vui lòng điền đầy đủ thông tin bắt buộc.")
                elif reg_password != confirm_password:
                    st.error("Mật khẩu nhập lại không khớp.")
                else:
                    # Kiểm tra email đã tồn tại chưa
                    email_exists, message = check_email_exists(reg_email)
                    
                    if email_exists:
                        st.error("Email này đã được sử dụng. Vui lòng chọn email khác.")
                    else:
                        # Đăng ký người dùng mới
                        success, message = register_user(reg_email, reg_password, full_name, class_name, "student")
                        if success:
                            st.success(message)
                            st.info("Vui lòng đăng nhập để tiếp tục.")
                        else:
                            st.error(message)

def main():
    st.set_page_config(
        page_title="Hệ thống kiểm tra sau đào tạo Đánh giá viên Nội bộ ISO 50001:2018",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Hiển thị logo trước khi bất kỳ nội dung nào khác
    display_logos()
    
    # Kiểm tra cấu hình Supabase
    is_valid, message = check_supabase_config()
    
    # Nếu chưa thiết lập biến môi trường
    if not is_valid:
        st.error(message)
        setup_environment_variables()
        return  # Dừng ứng dụng cho đến khi thiết lập biến môi trường
    
    # Thiết lập Supabase client
    supabase = get_supabase_client()
    if not supabase:
        st.error("Không thể kết nối đến Supabase. Vui lòng kiểm tra lại cấu hình.")
        setup_environment_variables()
        return
    
    # Sidebar - Menu điều hướng
    with st.sidebar:
        st.title("📝 Hệ thống kiểm tra sau đào tạo Đánh giá viên Nội bộ ISO 50001:2018")
        st.success("Đã kết nối thành công đến Supabase!")
        
        # Hiển thị thông tin dự án (ẩn key)
        with st.expander("Thông tin kết nối"):
            st.write(f"**URL:** {os.environ.get('SUPABASE_URL')}")
            api_key = os.environ.get('SUPABASE_KEY', '')
            masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "Chưa thiết lập"
            st.write(f"**API Key:** {masked_key}")
        
        # Kiểm tra đăng nhập
        if "user_role" not in st.session_state:
            st.session_state.user_role = None
            
        if "user_info" not in st.session_state:
            st.session_state.user_info = None
        
        # Nếu chưa đăng nhập
        if not st.session_state.user_role:
            # Sử dụng form đăng nhập/đăng ký
            login_register_form()
        
        # Đã đăng nhập - Hiển thị menu tương ứng
        else:
            st.write(f"Chào mừng bạn tham dự bài kiểm sau Đánh giá viên nội bộ ISO 50001:2018, **{st.session_state.user_info['full_name']}**!")
            
            # Menu cho quản trị viên
            if st.session_state.user_role == "admin":
                page = st.radio(
                    "Chọn chức năng:",
                    ["Quản lý câu hỏi", "Báo cáo & thống kê", "Quản trị hệ thống"]
                )
                        
            # Menu cho học viên
            else:
                page = st.radio(
                    "Chọn chức năng:",
                    ["Làm bài khảo sát"]
                )
            
            # Nút đăng xuất
            if st.button("Đăng xuất"):
                st.session_state.user_role = None
                st.session_state.user_info = None
                st.rerun()
    
    # Hiển thị nội dung tương ứng
    if "user_role" in st.session_state and st.session_state.user_role:
        if st.session_state.user_role == "admin":
            if page == "Quản lý câu hỏi":
                manage_questions()
            elif page == "Báo cáo & thống kê":
                stats_dashboard()
            elif page == "Quản trị hệ thống":
                report.view_statistics()
        else:
            if page == "Làm bài khảo sát":
                survey_form(
                    st.session_state.user_info["email"], 
                    st.session_state.user_info["full_name"], 
                    st.session_state.user_info["class_name"]
                )
    else:
        # Màn hình chào mừng
        st.header("Chào mừng các bạn học viên của khóa Đào tạo Đánh giá viên nội bộ ISO 50001:2018 - TUV NORD!")
        
        st.markdown("""
        ### Tính năng chính:
        
        **Dành cho học viên:**
        - Làm bài khảo sát với nhiều loại câu hỏi
        - Xem lịch sử làm bài và kết quả
        - Theo dõi tiến độ cải thiện
        
        **Dành cho quản trị viên:**
        - Quản lý câu hỏi: Thêm, sửa, xóa câu hỏi
        - Báo cáo & thống kê: Phân tích kết quả, xem báo cáo chi tiết
        - Quản trị hệ thống: Quản lý học viên, xuất dữ liệu
        
        Vui lòng đăng nhập hoặc đăng ký ở thanh bên trái để sử dụng hệ thống.
        """)
        
        # Hiển thị một số thông tin demo
        with st.expander("Thông tin App: Kiểm tra Đánh giá viên nội bộ ISO 50001:2018"):
            st.write("""
            **Đây là phiên bản App Ver 1.0 Team ISO 50001**
            
            - Nếu bạn đã có tài khoản, vui lòng đăng nhập.
            - Nếu chưa có tài khoản, vui lòng đăng ký để sử dụng hệ thống.
            
            Hệ thống này sử dụng Supabase làm cơ sở dữ liệu.
            """)

def setup_environment_variables():
    """Form thiết lập biến môi trường"""
    st.header("Thiết lập kết nối Supabase")
    
    # Tabs cho các phương pháp thiết lập khác nhau
    tab1, tab2 = st.tabs(["Thiết lập trực tiếp", "Hướng dẫn"])
    
    with tab1:
        st.subheader("Thiết lập biến môi trường")
        st.warning("Chú ý: Phương pháp này chỉ lưu biến môi trường trong phiên hiện tại. Khi khởi động lại ứng dụng, bạn sẽ cần thiết lập lại.")
        
        with st.form("env_setup_form"):
            current_url = os.environ.get("SUPABASE_URL", "")
            current_key = os.environ.get("SUPABASE_KEY", "")
            
            supabase_url = st.text_input("URL (Project URL)", value=current_url, placeholder="https://your-project-id.supabase.co")
            supabase_key = st.text_input("API Key (anon/public)", value=current_key, type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            
            st.info("Bạn có thể tìm thấy URL và API Key trong dashboard của Supabase: Cài đặt > API")
            
            submit = st.form_submit_button("Lưu cấu hình")
            
            if submit:
                if not supabase_url or not supabase_key:
                    st.error("Vui lòng nhập đầy đủ URL và API Key.")
                elif not supabase_url.startswith("https://"):
                    st.error("URL không hợp lệ. URL phải bắt đầu bằng https://")
                else:
                    os.environ["SUPABASE_URL"] = supabase_url
                    os.environ["SUPABASE_KEY"] = supabase_key
                    st.success("Đã thiết lập biến môi trường thành công!")
                    st.button("Tiếp tục", on_click=lambda: st.rerun())
    
    with tab2:
        st.subheader("Hướng dẫn thiết lập")
        
        st.markdown("""
        ### Thiết lập theo sự hướng dẫn      
        
        """)
        
        st.info("Sau khi thiết lập biến môi trường bằng một trong các phương pháp trên, hãy khởi động lại ứng dụng.")

if __name__ == "__main__":
    main()
