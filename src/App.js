import { BrowserRouter as Router, Routes, Route, useNavigate } from "react-router-dom";
import logo from './assets/ccpp-logo.svg';  // ✅ 로고 파일 변경
import './App.css';
// 실제 파일은 `src/` 루트에 존재하므로 경로를 수정합니다.
import Explore from './Explore';
import Jobs from './Jobs';
import StackBooks from './StackBooks';
import BookDetail from './BookDetail';

function Home() {
	const navigate = useNavigate(); // ✅ 페이지 이동용 hook

	// 임시 공고 데이터 (나중에 데이터베이스에서 가져올 예정)
	const announcements = [
		{ id: 1, title: "웹 개발자 채용공고", company: "테크 컴퍼니", deadline: "2025.12.31", isNew: true },
		{ id: 2, title: "프론트엔드 개발자", company: "스타트업", deadline: "2025.12.15", isNew: true },
	];

	return (
		<div className="App">
			<header className="header">
				<div className="logo">
					{/* ✅ 변경된 로고 적용 */}
					<img src={logo} alt="CCPP Logo" className="logo-image" />
				</div>
				<div className="search-container">
					<input type="text" placeholder="키워드 / 직무 검색" className="search-input" />
				</div>
			</header>

			<main className="main-content">
				<div className="content-layout">
					<div className="announcement-list">
						<h2>채용 공고</h2>
						<div className="announcement-items">
							{announcements.map(item => (
								<div key={item.id} className="announcement-item">
									<div className="announcement-header">
										<h3>{item.title}</h3>
										{item.isNew && <span className="new-badge">New</span>}
									</div>
									<div className="announcement-info">
										<span>{item.company}</span>
										<span className="deadline">마감일: {item.deadline}</span>
									</div>
								</div>
							))}
						</div>
						<button className="btn more-btn" onClick={() => navigate('/jobs')}>더보기</button>
					</div>

					<div className="explore-section">
						<div className="carousel">
							<div className="carousel-items">
								<img src="/images/book1.jpg" alt="Book 1" />
								<img src="/images/book2.jpg" alt="Book 2" />
								<img src="/images/book3.jpg" alt="Book 3" />
							</div>
							<div className="carousel-dots">
								<span className="dot active"></span>
								<span className="dot"></span>
								<span className="dot"></span>
								<span className="dot"></span>
							</div>
						</div>

						{/* ✅ 탐색하기 버튼 클릭 시 /explore 페이지로 이동 */}
						<button className="btn explore-btn" onClick={() => navigate("/explore")}>
							탐색하기
						</button>
					</div>
				</div>
			</main>
		</div>
	);
}

// Explore page moved to src/pages/Explore.js

function App() {
	return (
		<Router>
			<Routes>
				<Route path="/" element={<Home />} />
	<Route path="/explore" element={<Explore />} />
			<Route path="/jobs" element={<Jobs />} />
			<Route path="/stack/:stackName" element={<StackBooks />} />
			<Route path="/book/:id" element={<BookDetail />} />
			</Routes>
		</Router>
	);
}

export default App;
