import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import './Explore.css';

// Mock chart data per job group. Real data will be plugged later.
const GROUP_DATA = {
  backend: [
    { label: 'Java', value: 35, color: '#1f77b4' },
    { label: 'Spring', value: 25, color: '#ff7f0e' },
    { label: 'DB', value: 20, color: '#2ca02c' },
    { label: 'Kubernetes', value: 20, color: '#d62728' },
  ],
  frontend: [
    { label: 'React', value: 45, color: '#1f77b4' },
    { label: 'TypeScript', value: 30, color: '#ff7f0e' },
    { label: 'CSS', value: 25, color: '#2ca02c' },
  ],
  data: [
    { label: 'Python', value: 50, color: '#1f77b4' },
    { label: 'SQL', value: 30, color: '#ff7f0e' },
    { label: 'Spark', value: 20, color: '#2ca02c' },
  ],
  devops: [
    { label: 'Docker', value: 40, color: '#1f77b4' },
    { label: 'AWS', value: 35, color: '#ff7f0e' },
    { label: 'CI/CD', value: 25, color: '#2ca02c' },
  ],
};

// Mock books data (replace with real data later)
const BOOKS = [
  { id: 1, title: 'Practical Statistics for Data Scientists', author: 'Peter Bruce', price: '25,000', description: '실무 데이터 분석에 필요한 통계 개념과 예제를 제공합니다.' },
  { id: 2, title: 'Deep Learning with Python', author: "François Chollet", price: '30,000', description: '케라스 창시자가 알려주는 딥러닝 실전 안내서입니다.' },
  { id: 3, title: 'Designing Data-Intensive Applications', author: 'Martin Kleppmann', price: '35,000', description: '대규모 데이터 시스템 설계의 원칙과 패턴을 다룹니다.' },
  { id: 4, title: 'Clean Code', author: 'Robert C. Martin', price: '22,000', description: '좋은 코드와 소프트웨어 설계 습관을 배우는 고전입니다.' },
  { id: 5, title: "You Don't Know JS", author: 'Kyle Simpson', price: '18,000', description: '자바스크립트의 내부 동작을 깊게 이해하도록 돕습니다.' },
];

function PieChart({ data = [], size = 160 }) {
  // compute slices
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let cumulative = 0;
  const slices = data.map((d) => {
    const start = cumulative / total;
    cumulative += d.value;
    const end = cumulative / total;
    return { ...d, start, end };
  });

  const radius = size / 2;
  const center = size / 2;

  const polarToCartesian = (cx, cy, r, t) => {
    const angle = 2 * Math.PI * t - Math.PI / 2;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  };

  const arcPath = (start, end) => {
    const startPt = polarToCartesian(center, center, radius, start);
    const endPt = polarToCartesian(center, center, radius, end);
    const largeArcFlag = end - start <= 0.5 ? 0 : 1;
    return `M ${center} ${center} L ${startPt.x} ${startPt.y} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endPt.x} ${endPt.y} Z`;
  };

  return (
    <svg className="piechart" width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {slices.map((s, i) => (
  <path key={i} className="slice" style={{ '--i': i }} d={arcPath(s.start, s.end)} fill={s.color} stroke="#fff" strokeWidth="1" />
      ))}
      {/* center circle for donut look */}
      <circle cx={center} cy={center} r={radius * 0.45} fill="#ffffff" />
    </svg>
  );
}

export default function Explore() {
  const groups = Object.keys(GROUP_DATA);
  const [selected, setSelected] = useState(groups[0]);
  // Popup/modal behavior removed — book items are static now
  const navigate = useNavigate();

  const chartData = useMemo(() => GROUP_DATA[selected] || [], [selected]);

  return (
    <div className="explore-root">
      <header className="explore-header">
        <h1>탐색하기</h1>
        <button className="btn back-btn" onClick={() => navigate('/')}>홈으로</button>
      </header>

      <main className="explore-main">
        <section className="left-col">
          <div className="card">
            <h3>직군 선택</h3>
            <div className="tags">
              {groups.map((g) => (
                <button
                  key={g}
                  className={`tag ${selected === g ? 'active' : ''}`}
                  onClick={() => setSelected(g)}
                  aria-pressed={selected === g}
                  aria-label={`직군 ${g}`} 
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          <div className="card chart-card">
            <div className="chart-placeholder">
              <PieChart data={chartData} size={180} />
            </div>
          </div>
        </section>

        <section className="center-col">
          <div className="card">
            <h3>주요 기술 스택</h3>
            <div className="stack-list">
              {/* static placeholders for now (no data) */}
              <div className="stack-item">
                <div className="stack-title">Python</div>
                <button className="btn small">추천 자료</button>
              </div>
              <div className="stack-item">
                <div className="stack-title">React</div>
                <button className="btn small">추천 자료</button>
              </div>
              <div className="stack-item">
                <div className="stack-title">Kafka</div>
                <button className="btn small">추천 자료</button>
              </div>
            </div>
          </div>
        </section>

        <section className="right-col">
          <div className="card books-card">
            <h3>추천 도서 목록</h3>
            <div className="book-list">
              {BOOKS.map((b) => (
                <div key={b.id} className="book-item">
                  <div className="book-cover" />
                  <div className="book-info">
                    <div className="book-title">{b.title}</div>
                    <div className="book-meta">{b.author} · {b.price}</div>
                  </div>
                </div>
              ))}

            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
