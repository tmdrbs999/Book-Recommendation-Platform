import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './BookDetail.css';
import { getBookById } from './data/books';

export default function BookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const book = getBookById(id);

  if (!book) {
    return (
      <div className="book-root">
        <header className="book-header">
          <button className="btn back-btn" onClick={() => navigate(-1)}>뒤로</button>
          <h2>도서를 찾을 수 없습니다</h2>
        </header>
        <main className="book-main">
          <div className="card empty">해당 도서 정보를 찾을 수 없습니다.</div>
        </main>
      </div>
    );
  }

  return (
    <div className="book-root">
      <header className="book-header">
        <button className="btn back-btn" onClick={() => navigate(-1)}>뒤로</button>
        <h2>{book.title}</h2>
      </header>

      <main className="book-main">
        <div className="card book-detail-card">
          <div className="detail-grid">
            <div className="cover-placeholder" />
            <div className="detail-info">
              <div className="book-title large">{book.title}</div>
              <div className="book-author">{book.author}</div>
              <div className="book-desc">{book.description}</div>
              <div className="book-price">{book.price}</div>
              <div style={{marginTop:12}}>
                <button className="btn primary">구매하러 가기</button>
                <button className="btn" style={{marginLeft:8}} onClick={() => navigate(-1)}>목록으로</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
