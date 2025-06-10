"""Scripts JavaScript limpios y profesionales para el reporte HTML."""


class HTMLScripts:
    """Maneja los scripts JavaScript del reporte HTML con funcionalidad esencial."""

    @staticmethod
    def get_scripts() -> str:
        """Retorna los scripts JavaScript optimizados para interactividad profesional."""
        return """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialize core functionality
    initializeSidebar();
    initializeNavigation();
    initializeSearch();
    initializeKeyboardShortcuts();
    initializeResponsive();
    initializeTooltips();
    autoExpandBehavior();
});

function initializeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarTabs = document.querySelectorAll('.sidebar-tab');
    const sidebarPanels = document.querySelectorAll('.sidebar-panel');
    const contentPanels = document.querySelectorAll('.main-content-panel');

    // Tab switching functionality
    sidebarTabs.forEach((tab, index) => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs and panels
            sidebarTabs.forEach(t => t.classList.remove('active'));
            sidebarPanels.forEach(p => p.classList.remove('active'));

            // Add active class to clicked tab and corresponding panel
            this.classList.add('active');
            if (sidebarPanels[index]) {
                sidebarPanels[index].classList.add('active');
            }

            // Control main content based on data-content attribute
            const contentType = this.getAttribute('data-content');
            if (contentType) {
                switchMainContent(contentType);
            }

            // Save active tab
            localStorage.setItem('active-sidebar-tab', index);

            // If sidebar is collapsed, expand it when tab is clicked
            const container = document.querySelector('.container');
            if (container && container.classList.contains('sidebar-collapsed')) {
                toggleSidebar();
            }
        });
    });

    // Restore saved active tab or default to first tab
    const savedTab = localStorage.getItem('active-sidebar-tab');
    let activeTabIndex = 0; // Default to explorer tab

    if (savedTab !== null && parseInt(savedTab) < sidebarTabs.length) {
        activeTabIndex = parseInt(savedTab);
    }

    // Ensure only the correct tab and panel are active
    sidebarTabs.forEach((tab, index) => {
        tab.classList.remove('active');
        if (index === activeTabIndex) {
            tab.classList.add('active');
        }
    });

    sidebarPanels.forEach((panel, index) => {
        panel.classList.remove('active');
        if (index === activeTabIndex) {
            panel.classList.add('active');
        }
    });

    // Set initial main content based on the active tab
    const activeTab = sidebarTabs[activeTabIndex];
    if (activeTab) {
        const contentType = activeTab.getAttribute('data-content');
        if (contentType) {
            switchMainContent(contentType);
        }
    }

    // Restore saved sidebar state
    const savedCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (savedCollapsed) {
        toggleSidebar();
    }
}

function switchMainContent(contentType) {
    const contentPanels = document.querySelectorAll('.main-content-panel');
    
    // Hide all content panels
    contentPanels.forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Show the appropriate content panel
    const targetPanel = document.getElementById(`content-${contentType}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
    }
    
    // Save active content type
    localStorage.setItem('active-main-content', contentType);
}

// Global function to switch main tabs (called from navigation) - now controls sidebar
function switchMainTab(tabName) {
    // Map content names to sidebar tab indices
    const contentMap = {
        'analysis': 0,      // Explorer tab
        'metrics-docs': 2   // Metrics tab
    };
    
    const tabIndex = contentMap[tabName];
    if (tabIndex !== undefined) {
        const targetTab = document.querySelectorAll('.sidebar-tab')[tabIndex];
        if (targetTab) {
            targetTab.click();
        }
    }
}

function toggleSidebar() {
    const container = document.querySelector('.container');
    const sidebar = document.querySelector('.sidebar');
    const isCollapsed = container.classList.contains('sidebar-collapsed');

    if (isCollapsed) {
        container.classList.remove('sidebar-collapsed');
        sidebar.classList.remove('collapsed');
    } else {
        container.classList.add('sidebar-collapsed');
        sidebar.classList.add('collapsed');
    }

    // Save preference
    localStorage.setItem('sidebar-collapsed', !isCollapsed);
}

function initializeNavigation() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Update active nav item
                updateActiveNavItem(this.getAttribute('href'));
            }
        });
    });

    // Highlight active section on scroll
    highlightActiveSection();
}

function updateActiveNavItem(href) {
    document.querySelectorAll('.nav-list a').forEach(link => {
        link.classList.remove('active');
    });

    const activeLink = document.querySelector(`.nav-list a[href="${href}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

function highlightActiveSection() {
    const sections = document.querySelectorAll('[id]');
    const navLinks = document.querySelectorAll('.nav-list a[href^="#"]');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
                const id = entry.target.id;
                const activeLink = document.querySelector(`.nav-list a[href="#${id}"]`);

                // Remove active class from all nav links
                navLinks.forEach(link => link.classList.remove('active'));

                // Add active class to current section link
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        });
    }, {
        threshold: [0.1, 0.3, 0.5],
        rootMargin: '-10% 0px -60% 0px'
    });

    sections.forEach(section => observer.observe(section));
}

function initializeSearch() {
    const searchInput = document.getElementById('module-search');
    if (!searchInput) return;

    const explorerContent = document.querySelector('.explorer-content');
    if (!explorerContent) return;

    // Store the original content to restore when search is cleared
    const originalContent = explorerContent.innerHTML;

    let searchTimeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.toLowerCase().trim();

        // Debounce search
        searchTimeout = setTimeout(() => {
            performHierarchicalSearch(query, explorerContent, originalContent);
        }, 150);
    });

    // Clear search on escape
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            this.value = '';
            explorerContent.innerHTML = originalContent;
            this.blur();
        }
    });
}

function performHierarchicalSearch(query, explorerContent, originalContent) {
    if (query.length < 2) {
        // Restore original content when search is empty
        explorerContent.innerHTML = originalContent;
        return;
    }

    // Clone the original content to work with
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = originalContent;

    // Find all matching elements (modules and folders)
    const allLinks = tempContainer.querySelectorAll('a[href], .package-header .folder-content');
    const matchingElements = new Set();
    const ancestorElements = new Set();

    // Find direct matches
    allLinks.forEach(element => {
        const text = element.textContent.toLowerCase();
        const title = (element.getAttribute('title') || '').toLowerCase();

        if (text.includes(query) || title.includes(query)) {
            matchingElements.add(element);
            // Add all ancestors of matching elements
            addAncestorsToSet(element, ancestorElements);
        }
    });

    // Filter the hierarchy: remove elements that don't match and don't contain matches
    filterHierarchy(tempContainer, matchingElements, ancestorElements);

    // Highlight search terms in the filtered content
    highlightSearchTermsInHierarchy(tempContainer, query);

    // Update the explorer content
    explorerContent.innerHTML = tempContainer.innerHTML;

    // Auto-expand filtered results
    tempContainer.querySelectorAll('details').forEach(details => {
        details.open = true;
    });

    // Copy the open state to the actual DOM
    explorerContent.querySelectorAll('details').forEach(details => {
        details.open = true;
    });
}

function addAncestorsToSet(element, ancestorSet) {
    let current = element.parentElement;
    while (current) {
        if (current.classList.contains('package-group') ||
            current.classList.contains('package-tree') ||
            current.classList.contains('explorer-content')) {
            ancestorSet.add(current);
        }
        current = current.parentElement;
    }
}

function filterHierarchy(container, matchingElements, ancestorElements) {
    // Remove non-matching package groups and files
    const packageGroups = container.querySelectorAll('.package-group');
    packageGroups.forEach(group => {
        const hasMatchingDescendants = hasMatchingContent(group, matchingElements, ancestorElements);
        if (!hasMatchingDescendants) {
            group.remove();
        }
    });

    // Remove non-matching files from module lists
    const moduleListItems = container.querySelectorAll('.module-list li');
    moduleListItems.forEach(item => {
        const link = item.querySelector('a');
        if (link && !matchingElements.has(link)) {
            item.remove();
        }
    });

    // Remove empty package groups
    container.querySelectorAll('.package-group').forEach(group => {
        const hasContent = group.querySelector('.module-list li') ||
                          group.querySelector('.package-group');
        if (!hasContent) {
            group.remove();
        }
    });
}

function hasMatchingContent(element, matchingElements, ancestorElements) {
    // Check if this element or any descendant is a match or ancestor
    if (ancestorElements.has(element)) {
        return true;
    }

    // Check for matching links within this element
    const links = element.querySelectorAll('a');
    for (const link of links) {
        if (matchingElements.has(link)) {
            return true;
        }
    }

    // Check for matching folder headers
    const folderHeaders = element.querySelectorAll('.folder-content');
    for (const header of folderHeaders) {
        if (matchingElements.has(header)) {
            return true;
        }
    }

    return false;
}

function highlightSearchTermsInHierarchy(container, query) {
    if (!query || query.length < 2) return;

    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');

    // Highlight in links and headers
    container.querySelectorAll('a, .folder-content').forEach(element => {
        if (element.children.length === 0) { // Only text nodes
            const originalText = element.textContent;
            if (originalText.toLowerCase().includes(query)) {
                element.innerHTML = originalText.replace(regex, '<mark style="background: var(--color-secondary); color: white; padding: 1px 2px; border-radius: 2px;">$1</mark>');
            }
        } else {
            // Handle elements with children (like icons)
            const walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {
                if (node.nodeValue.trim()) {
                    textNodes.push(node);
                }
            }

            textNodes.forEach(textNode => {
                if (textNode.nodeValue.toLowerCase().includes(query)) {
                    const span = document.createElement('span');
                    span.innerHTML = textNode.nodeValue.replace(regex, '<mark style="background: var(--color-secondary); color: white; padding: 1px 2px; border-radius: 2px;">$1</mark>');
                    textNode.parentNode.replaceChild(span, textNode);
                }
            });
        }
    });
}

function initializeResponsive() {
    // Mobile sidebar handling
    if (window.innerWidth <= 768) {
        setupMobileSidebar();
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            setupMobileSidebar();
        } else {
            cleanupMobileSidebar();
        }
    });
}

function setupMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');

    // Create mobile overlay if it doesn't exist
    let overlay = document.querySelector('.mobile-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'mobile-overlay';
        document.body.appendChild(overlay);

        overlay.addEventListener('click', function() {
            toggleMobileSidebar();
        });
    }
}

function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');

    const isOpen = sidebar.classList.contains('mobile-open');

    if (isOpen) {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    } else {
        sidebar.classList.add('mobile-open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function cleanupMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');

    sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
}

function autoExpandBehavior() {
    // Auto-expand first file with errors
    const errorFile = document.querySelector('.file-header.error');
    if (errorFile) {
        const details = errorFile.closest('details');
        if (details) {
            details.open = true;
            setTimeout(() => {
                errorFile.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        }
    }

    // Expand packages by default if few files
    const totalFiles = document.querySelectorAll('.file-analysis').length;
    if (totalFiles <= 20) {
        document.querySelectorAll('.package-group').forEach(details => {
            details.open = true;
        });
    }

    // Auto-expand first package in explorer if only a few packages
    const packageGroups = document.querySelectorAll('.package-group');
    if (packageGroups.length <= 5) {
        packageGroups.forEach(group => group.open = true);
    }
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F para enfocar búsqueda
        if ((e.ctrlKey || e.metaKey) && e.key === 'f' && !e.shiftKey) {
            const searchInput = document.getElementById('module-search');
            if (searchInput) {
                e.preventDefault();

                // Switch to explorer tab (no need to search for specific tab since search is integrated)
                const explorerTab = document.querySelector('.sidebar-tab[data-panel="explorer"]');
                if (explorerTab) explorerTab.click();

                searchInput.focus();
                searchInput.select();
            }
        }

        // Ctrl/Cmd + B para toggle sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            if (window.innerWidth <= 768) {
                toggleMobileSidebar();
            } else {
                toggleSidebar();
            }
        }

        // ? para mostrar ayuda de atajos
        if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault();
            showKeyboardHelp();
        }

        // Numbers 1-3 para cambiar tabs del sidebar
        if (['1', '2', '3'].includes(e.key) && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            const tabIndex = parseInt(e.key) - 1;
            const tab = document.querySelectorAll('.sidebar-tab')[tabIndex];
            if (tab) tab.click();
        }

        // Shortcuts específicos para cambiar contenido
        if ((e.ctrlKey || e.metaKey) && e.key === 'a' && !e.shiftKey) {
            e.preventDefault();
            // Switch to analysis (Explorer tab)
            const explorerTab = document.querySelector('.sidebar-tab[data-content="analysis"]');
            if (explorerTab) explorerTab.click();
        }

        if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
            e.preventDefault();
            // Switch to metrics documentation
            const metricsTab = document.querySelector('.sidebar-tab[data-content="metrics-docs"]');
            if (metricsTab) metricsTab.click();
        }

        // Escape para cerrar modales y limpiar búsqueda
        if (e.key === 'Escape') {
            const modal = document.querySelector('.keyboard-help-modal');
            if (modal) {
                modal.remove();
                return;
            }

            if (window.innerWidth <= 768) {
                const sidebar = document.querySelector('.sidebar');
                if (sidebar && sidebar.classList.contains('mobile-open')) {
                    toggleMobileSidebar();
                }
            }
        }
    });
}

function showKeyboardHelp() {
    // Remove existing modal if any
    const existingModal = document.querySelector('.keyboard-help-modal');
    if (existingModal) existingModal.remove();

    const helpModal = document.createElement('div');
    helpModal.className = 'keyboard-help-modal';
    helpModal.innerHTML = `
        <div class="modal-backdrop" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
            <div class="modal-content" style="background: var(--color-surface); padding: 2rem; border-radius: var(--border-radius-xl); max-width: 500px; box-shadow: var(--shadow-lg); border: 1px solid var(--color-border);">
                <h3 style="margin-bottom: 1.5rem; color: var(--color-primary); display: flex; align-items: center; gap: 0.5rem;">
                    ⌨️ Atajos de Teclado
                </h3>
                <div style="display: grid; gap: 1rem;">
                    <div class="shortcut-group">
                        <h4 style="color: var(--color-secondary); margin-bottom: 0.5rem; font-size: 1rem;">Navegación</h4>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--color-border);">
                            <span>Buscar módulos</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">Ctrl+F</kbd>
                        </div>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--color-border);">
                            <span>Toggle sidebar</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">Ctrl+B</kbd>
                        </div>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--color-border);">
                            <span>Cambiar tab sidebar</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">Ctrl+1/2/3</kbd>
                        </div>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--color-border);">
                            <span>Ver análisis del proyecto</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">Ctrl+A</kbd>
                        </div>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--color-border);">
                            <span>Ver documentación métricas</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">Ctrl+M</kbd>
                        </div>
                    </div>

                    <div class="shortcut-group">
                        <h4 style="color: var(--color-secondary); margin-bottom: 0.5rem; font-size: 1rem;">General</h4>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--color-border);">
                            <span>Mostrar esta ayuda</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">?</kbd>
                        </div>
                        <div class="shortcut-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0;">
                            <span>Cerrar modal/menú</span>
                            <kbd style="background: var(--color-background); padding: 0.25rem 0.5rem; border-radius: var(--border-radius-sm); font-family: var(--font-family-mono); border: 1px solid var(--color-border);">Esc</kbd>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 1.5rem; text-align: center;">
                    <button onclick="this.closest('.keyboard-help-modal').remove()"
                            style="padding: 0.75rem 1.5rem; background: var(--color-secondary); color: white; border: none; border-radius: var(--border-radius-md); cursor: pointer; font-size: 0.9rem; transition: background-color var(--transition-fast);">
                        Cerrar
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(helpModal);

    // Close on backdrop click
    helpModal.querySelector('.modal-backdrop').addEventListener('click', function(e) {
        if (e.target === this) {
            helpModal.remove();
        }
    });

    // Auto-focus close button
    const closeButton = helpModal.querySelector('button');
    setTimeout(() => closeButton.focus(), 100);
}

function showAnalysisHelp(analysisType, thresholdProfile = 'normal') {
    // Remove existing modal if any
    const existingModal = document.querySelector('.analysis-help-modal');
    if (existingModal) existingModal.remove();

    let content = '';
    let title = '';
    let icon = '';

    if (analysisType === 'basic') {
        icon = '🎯';

        if (thresholdProfile === 'permissive') {
            title = 'Análisis de Calidad - Detección Inclusiva';
            content = `
                <h4>¿Qué es este análisis?</h4>
                <p>Este análisis inclusivo está configurado para detectar la <strong>mayor cantidad de problemas posibles</strong>, incluyendo los más leves.</p>

                <h4>Configuración actual:</h4>
                <ul>
                    <li><strong>Threshold Profile:</strong> Permissive</li>
                    <li><strong>Thresholds LOW:</strong> Utiliza umbrales muy bajos para capturar incluso problemas menores</li>
                    <li><strong>Filosofía:</strong> "Es mejor detectar un falso positivo que perderse un problema real"</li>
                    <li><strong>Algoritmo simple:</strong> Cálculo directo basado en proporción de entidades problemáticas</li>
                </ul>

                <h4>¿Cuándo usar este perfil?</h4>
                <ul>
                    <li>Durante el aprendizaje y mejora de buenas prácticas</li>
                    <li>En proyectos donde se quiere ser muy estricto con la calidad</li>
                    <li>Para detectar todos los posibles puntos de mejora</li>
                    <li>En auditorías exhaustivas de código</li>
                </ul>

                <h4>Nota:</h4>
                <p>Este perfil puede generar más alertas de las necesarias en proyectos maduros, pero es excelente para elevar estándares de calidad.</p>
            `;
        } else { // normal
            title = 'Análisis de Calidad - Detección Balanceada';
            content = `
                <h4>¿Qué es este análisis?</h4>
                <p>Este análisis balanceado está diseñado para la <strong>detección equilibrada</strong> de problemas de calidad en tu código.</p>

                <h4>Configuración actual:</h4>
                <ul>
                    <li><strong>Threshold Profile:</strong> Normal</li>
                    <li><strong>Thresholds MEDIUM:</strong> Utiliza umbrales moderados para detectar problemas significativos</li>
                    <li><strong>Filosofía:</strong> Balance entre detección temprana y ruido</li>
                    <li><strong>Algoritmo simple:</strong> Cálculo directo basado en proporción de entidades problemáticas</li>
                </ul>

                <h4>¿Cuándo usar este perfil?</h4>
                <ul>
                    <li>Durante el desarrollo para monitoreo continuo</li>
                    <li>En proyectos en desarrollo activo</li>
                    <li>Como evaluación estándar de calidad</li>
                    <li>Para equipos que buscan un balance práctico</li>
                </ul>

                <h4>Complemento:</h4>
                <p>En este perfil también se muestra el <strong>Análisis Avanzado</strong> para comparar con criterios más estrictos.</p>
            `;
        }
    } else if (analysisType === 'advanced') {
        title = 'Análisis Avanzado - Detección Crítica';
        icon = '🔍';
        content = `
            <h4>¿Qué es este análisis?</h4>
            <p>Este análisis avanzado está diseñado para la <strong>detección crítica</strong> de problemas serios de calidad.</p>

            <h4>Características principales:</h4>
            <ul>
                <li><strong>Thresholds HIGH:</strong> Utiliza umbrales estrictos que solo detectan problemas realmente serios</li>
                <li><strong>Ponderación 3x:</strong> Las entidades de alta complejidad pesan 3 veces más en el cálculo</li>
                <li><strong>Algoritmo sofisticado:</strong> Evaluación más precisa de la calidad real del código</li>
                <li><strong>Más estricto:</strong> Solo reporta problemas que requieren atención inmediata</li>
            </ul>

            <h4>¿Cuándo usar este análisis?</h4>
            <ul>
                <li>Para evaluaciones finales antes de producción</li>
                <li>En proyectos maduros con altos estándares</li>
                <li>Para identificar hotspots críticos de refactoring</li>
                <li>En auditorías de calidad de código</li>
            </ul>

            <h4>Threshold Profiles:</h4>
            <ul>
                <li><strong>Normal:</strong> Se muestra junto al análisis básico para comparación</li>
                <li><strong>Strict:</strong> Es el único análisis mostrado (solo problemas críticos)</li>
            </ul>

            <h4>Nota importante:</h4>
            <p>Los scores pueden ser significativamente diferentes al análisis básico debido a los criterios más estrictos.</p>
        `;
    }

    const helpModal = document.createElement('div');
    helpModal.className = 'analysis-help-modal';
    helpModal.innerHTML = `
        <div class="analysis-help-content">
            <h3>${icon} ${title}</h3>
            ${content}
            <button class="analysis-help-close" onclick="this.closest('.analysis-help-modal').remove()">
                Cerrar
            </button>
        </div>
    `;

    document.body.appendChild(helpModal);

    // Close on backdrop click
    helpModal.addEventListener('click', function(e) {
        if (e.target === this) {
            helpModal.remove();
        }
    });

    // Auto-focus close button
    const closeButton = helpModal.querySelector('.analysis-help-close');
    setTimeout(() => closeButton.focus(), 100);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
}

function initializeTooltips() {
    // Crear un elemento tooltip personalizado
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.style.cssText = `
        position: absolute;
        background: var(--color-primary);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
        z-index: 1000;
        max-width: 300px;
        word-wrap: break-word;
        line-height: 1.4;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.2);
    `;
    document.body.appendChild(tooltip);

    // Agregar eventos a todos los elementos con tooltip
    const tooltipElements = document.querySelectorAll('[title]');

    tooltipElements.forEach(element => {
        const originalTitle = element.getAttribute('title');

        // Remover el title original para evitar tooltip nativo
        element.removeAttribute('title');
        element.setAttribute('data-tooltip', originalTitle);

        element.addEventListener('mouseenter', function(e) {
            const tooltipText = e.target.getAttribute('data-tooltip');
            if (tooltipText) {
                tooltip.textContent = tooltipText;
                tooltip.style.opacity = '1';

                // Posicionar el tooltip
                const rect = e.target.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();

                let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                let top = rect.top - tooltipRect.height - 8;

                // Ajustar si se sale de la pantalla
                if (left < 10) left = 10;
                if (left + tooltipRect.width > window.innerWidth - 10) {
                    left = window.innerWidth - tooltipRect.width - 10;
                }

                if (top < 10) {
                    top = rect.bottom + 8;
                }

                tooltip.style.left = left + window.scrollX + 'px';
                tooltip.style.top = top + window.scrollY + 'px';
            }
        });

        element.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
        });

        element.addEventListener('mousemove', function(e) {
            // Seguir el cursor para tooltips largos
            const tooltipText = e.target.getAttribute('data-tooltip');
            if (tooltipText && tooltipText.length > 100) {
                const rect = e.target.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();

                let left = e.clientX - (tooltipRect.width / 2);
                let top = e.clientY - tooltipRect.height - 15;

                // Ajustar límites
                if (left < 10) left = 10;
                if (left + tooltipRect.width > window.innerWidth - 10) {
                    left = window.innerWidth - tooltipRect.width - 10;
                }

                if (top < 10) {
                    top = e.clientY + 20;
                }

                tooltip.style.left = left + window.scrollX + 'px';
                tooltip.style.top = top + window.scrollY + 'px';
            }
        });
    });
}
</script>
"""
