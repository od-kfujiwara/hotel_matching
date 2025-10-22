// DOM Elements
const tourIdInput = document.getElementById('tour-id');
const airtripIdInput = document.getElementById('airtrip-id');
const matchingMethodSelect = document.getElementById('matching-method');
const thresholdInput = document.getElementById('threshold');
const thresholdValue = document.getElementById('threshold-value');
const processBtn = document.getElementById('process-btn');
const processStatus = document.getElementById('process-status');

const resultsSummary = document.getElementById('results-summary');
const matchesContainer = document.getElementById('matches-container');

const methodThresholds = {
    hash: 0.90,
    phash: 0.70,
    feature: 0.04,
    clip: 0.80,
    gemini: 0.80,
};

const methodDisplayNames = {
    hash: '平均ハッシュ法',
    phash: 'pHash (離散コサイン変換)',
    feature: '特徴点マッチング (ORB+RANSAC)',
    clip: 'CLIP (ViT-B/32)',
    gemini: 'Gemini (AI判定)',
};

const decisionLabels = {
    same: '一致',
    different: '不一致',
    uncertain: '判断保留',
};

// Event Listeners
processBtn.addEventListener('click', handleProcess);
thresholdInput.addEventListener('input', (e) => {
    thresholdValue.textContent = parseFloat(e.target.value).toFixed(2);
});

// マッチング方法が変更されたときに閾値を自動調整
matchingMethodSelect.addEventListener('change', (e) => {
    const method = e.target.value;
    const defaultThreshold = methodThresholds[method];
    if (defaultThreshold !== undefined) {
        thresholdInput.value = defaultThreshold;
        thresholdValue.textContent = defaultThreshold.toFixed(2);
    }
});

// Utility Functions
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message show ${type}`;
}

function hideStatus(element) {
    element.className = 'status-message';
}

function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span>処理中...';
    } else {
        button.disabled = false;
        button.textContent = '画像を取得して比較';
    }
}

function renderImageCell(name, fallbackLabel) {
    if (name) {
        return `
            <div class="match-image">
                <img src="/images/${name}" alt="${name}">
                <div class="label">${name}</div>
            </div>
        `;
    }
    return `
        <div class="match-image">
            <div class="label">${fallbackLabel}</div>
        </div>
    `;
}

// Process: Scrape and Compare
async function handleProcess() {
    const tourId = tourIdInput.value.trim();
    const airtripId = airtripIdInput.value.trim();
    const threshold = parseFloat(thresholdInput.value);
    const method = matchingMethodSelect.value;

    if (!tourId || !airtripId) {
        showStatus(processStatus, '両方のホテルIDを入力してください', 'error');
        return;
    }

    setButtonLoading(processBtn, true);
    resultsSummary.innerHTML = '';
    matchesContainer.innerHTML = '';

    try {
        // Step 1: Show progress - Fetching from tour.ne.jp
        showStatus(processStatus, '📥 tour.ne.jpから画像を取得中...', 'loading');
        await new Promise(resolve => setTimeout(resolve, 100)); // Allow UI update

        // Step 2: Show progress - Fetching from airtrip.jp (will happen on server)
        setTimeout(() => {
            showStatus(processStatus, '📥 airtrip.jpから画像を取得中...', 'loading');
        }, 1000);

        // Step 3: Show progress - Comparing
        setTimeout(() => {
            showStatus(processStatus, '🔍 画像を比較中...', 'loading');
        }, 2000);

        // Make the API call
        const response = await fetch('/api/scrape_and_compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tour_id: tourId,
                airtrip_id: airtripId,
                threshold,
                method
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'エラーが発生しました');
        }

        showStatus(processStatus, `✓ 処理が完了しました！`, 'success');

        // マッチング方法の表示名を取得
        const methodName = methodDisplayNames[method] || method;

        // Display summary
        const summaryHtml = `
            <h3>📈 サマリー</h3>
            <p><strong>マッチング方法:</strong> ${methodName}</p>
            <p><strong>tour.ne.jpの画像数:</strong> ${data.tour_count}枚</p>
            <p><strong>airtrip.jpの画像数:</strong> ${data.airtrip_count}枚</p>
            <p><strong>総比較回数:</strong> ${data.total_comparisons}回</p>
            <p><strong>類似度閾値:</strong> ${data.threshold.toFixed(2)}</p>
            <p style="font-size: 1.2rem; color: #667eea; margin-top: 10px;">
                <strong>一致した画像ペア:</strong> ${data.match_count}組
            </p>
        `;
        resultsSummary.innerHTML = summaryHtml;

        // Display matches
        if (data.matches.length > 0) {
            matchesContainer.innerHTML = data.matches.map((match, index) => {
                if (match.method === 'gemini') {
                    const decisionKey = (match.decision || '').toLowerCase();
                    const decisionLabel = decisionLabels[decisionKey] || decisionLabels.uncertain;
                    const scoreText = typeof match.similarity === 'number'
                        ? `${(match.similarity * 100).toFixed(2)}%`
                        : 'N/A';
                    const reasonText = (match.reason || '---').toString().replace(/\n/g, '<br>');
                    const tourImageName = match.image1 || (Array.isArray(match.tour_images) ? match.tour_images[0] : '');
                    const airtripImageName = match.image2 || (Array.isArray(match.airtrip_images) ? match.airtrip_images[0] : '');
                    return `
                        <div class="match-item">
                            <div class="match-header">
                                #${index + 1} - AI判定: ${decisionLabel}（スコア: ${scoreText}）
                            </div>
                            <div class="match-content">
                                ${renderImageCell(tourImageName, 'tour.ne.jpの画像がありません')}
                                ${renderImageCell(airtripImageName, 'airtrip.jpの画像がありません')}
                            </div>
                            <div style="margin-top: 12px; color: #555;">
                                <strong>コメント:</strong> ${reasonText}
                            </div>
                        </div>
                    `;
                }

                let detailInfo = '';
                if (match.method === 'hash' || match.method === 'phash') {
                    detailInfo = `ハッシュ距離: ${match.hash_distance}`;
                } else if (match.method === 'feature') {
                    detailInfo = `インライア: ${match.inlier_count}/${match.total_matches} (${(match.inlier_ratio * 100).toFixed(1)}%)`;
                } else if (match.method === 'clip') {
                    if (match.clip_model) {
                        detailInfo = `モデル: ${match.clip_model}`;
                    }
                }
                const detailInfoText = detailInfo ? ` (${detailInfo})` : '';

                return `
                    <div class="match-item">
                        <div class="match-header">
                            #${index + 1} - 類似度: ${(match.similarity * 100).toFixed(2)}%${detailInfoText}
                        </div>
                        <div class="match-content">
                            <div class="match-image">
                                <img src="/images/${match.image1}" alt="${match.image1}">
                                <div class="label">${match.image1}</div>
                            </div>
                            <div class="match-image">
                                <img src="/images/${match.image2}" alt="${match.image2}">
                                <div class="label">${match.image2}</div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            matchesContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #999;">
                    一致する画像が見つかりませんでした。<br>
                    閾値を下げてみてください。
                </div>
            `;
        }

    } catch (error) {
        showStatus(processStatus, `✗ エラー: ${error.message}`, 'error');
    } finally {
        setButtonLoading(processBtn, false);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Hotel Image Matching Tool initialized');
});
