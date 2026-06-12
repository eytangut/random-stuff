const yearNode = document.querySelector('#year');

if (yearNode) {
  yearNode.textContent = new Date().getFullYear();
}

for (const book of document.querySelectorAll('.book')) {
  book.addEventListener('mousemove', (event) => {
    const rect = book.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width - 0.5;
    const py = (event.clientY - rect.top) / rect.height - 0.5;
    book.style.transform = `translateY(-5px) rotateX(${(-py * 5).toFixed(2)}deg) rotateY(${(px * 6).toFixed(2)}deg)`;
  });

  book.addEventListener('mouseleave', () => {
    book.style.transform = '';
  });
}
